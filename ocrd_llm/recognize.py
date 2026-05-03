from ocrd import Processor
from ocrd.processor.base import OcrdPageResult
from ocrd_models.ocrd_page import (
    OcrdPage as PcGtsType, TextEquivType, TextLineType
)
import os
from PIL import Image
import base64
import io
from openai import OpenAI


class OcrdLLM(Processor):
    max_workers = 1

    @property
    def executable(self) -> str:
        return "ocrd-llm"

    def setup(self):
        self.params = dict(self.parameter or {})

        self.model_id = self.params['model_id']
        self.api_key = self.params['api_key']
        self.api_endpoint = self.params['api_endpoint']

        self.client = OpenAI(api_key=self.api_key, base_url=self.api_endpoint)


    def process_page_pcgts(self, *input_pcgts: PcGtsType, page_id: str | None = None) -> OcrdPageResult:
        """
        input_pcgts[0]: PageXML with textlines
        Return a new PageXML
        """

        assert len(input_pcgts) == 1, "Expect exactly 1 input PageXML files (lines)"

        prompt_txt_file = self.params['prompt_txt_file']
        if os.path.isabs(prompt_txt_file):
            prompt_path = prompt_txt_file
        else:
            prompt_path = os.path.join(self.workspace.directory, prompt_txt_file)

        self.prompt = ""
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                self.prompt = f.read().strip()
        except:
            raise FileNotFoundError(f"Prompt text file could not be read {prompt_path}")

        lines_doc = input_pcgts[0]

        output_doc: PcGtsType = self.recognize_text(lines_doc, page_id=page_id or "")

        return OcrdPageResult(pcgts=output_doc)
    
    def recognize_text(self, lines_doc: PcGtsType, page_id: str):
        """
        Main function.
        """

        # Create output document from the lines PageXML document.
        out_doc = lines_doc
        out_page = out_doc.get_Page()

        page_image, page_coords, _ = self.workspace.image_from_page(out_page, page_id)

        all_lines = out_page.get_AllTextLines()

        print(f"{page_id} has {len(all_lines)} TextLine elements")

        all_regions = out_page.get_AllRegions(classes=["Text"])

        # To crop TextLine images, the parent TextRegion elements need to be obtained.
        for text_region in all_regions:
            lines = text_region.get_TextLine() or []
            if len(lines) < 1:
                continue
            
            print(f"Crop TextRegion {text_region.id}")
            text_region_image, text_region_coords = self.workspace.image_from_segment(
                text_region, page_image, page_coords
            )

            for line in lines:
                try:
                    # Extract TextLine from the parent TextRegion
                    print(f"Crop TextLine {line.id}")
                    line_image, _ = self.workspace.image_from_segment(
                        line, text_region_image, text_region_coords
                    )

                    self._predict_text(text_region_image, line_image, line)

                except Exception as e:
                    print(f"Error while croping images {e}")
                    continue

        # out_doc.set_Metadata({"model_id": self.params['model_id']})

        return out_doc
    
    def _predict_text(self, textregion_image: Image.Image, textline_image: Image.Image, line: TextLineType):
        """
        Run text recognition and write text to TextLine elements.
        """

        base64_textline_image = self.image_to_base64(textline_image)

        base64_textregion_image = self.image_to_base64(textregion_image)

        generated_text = ""

        # TODO: Set temperature via ocrd-tool.json
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_textline_image
                                },
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": base64_textregion_image
                                },
                            },
                        ],
                    }
                ],
                temperature=0.7
            )
            generated_text = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error while recognizing text {e}")
        
        print(f"Generated text: {generated_text}")

        if line.get_TextEquiv():
            line.set_TextEquiv([])
        line.add_TextEquiv(TextEquivType(Unicode=generated_text))

    def image_to_base64(self, img: Image.Image) -> str:
        format_ = img.format or "PNG"  # fallback

        buffer = io.BytesIO()
        img.save(buffer, format=format_, quality=95)
        buffer.seek(0)

        base64_str = base64.b64encode(buffer.read()).decode('utf-8')

        mime_type = f"image/{format_.lower()}"
        if format_.upper() == "JPEG":
            mime_type = "image/jpeg"              

        return f"data:{mime_type};base64,{base64_str}"
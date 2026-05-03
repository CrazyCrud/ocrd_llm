import click
from ocrd.decorators import ocrd_cli_options, ocrd_cli_wrap_processor
from .recognize import OcrdLLM


@click.command()
@ocrd_cli_options
def ocrd_llm(*args, **kwargs):
    """
    CLI entrypoint for ocrd-llm.
    """

    return ocrd_cli_wrap_processor(OcrdLLM, *args, **kwargs)


if __name__ == "__main__":
    ocrd_llm()
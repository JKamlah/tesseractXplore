import click
from click_help_colors import HelpColorsCommand

from naturtag.image_metadata import get_keyword_metadata, write_metadata
from naturtag.inat_darwincore import get_observation_dwc_terms
from naturtag.inat_keywords import get_keywords
from naturtag.cli_utils import GlobPath, chain_lists, colorize_help_text, strip_url


@click.command(cls=HelpColorsCommand, help_headers_color='blue', help_options_color='cyan')
@click.pass_context
@click.option('-c', '--common-names', is_flag=True,
              help='Include common names for all ranks that have them')
@click.option('-h', '--hierarchical', is_flag=True,
              help='Generate pipe-delimited hierarchical keywords')
@click.option('-o', '--observation', help='Observation ID or URL', callback=strip_url)
@click.option('-t', '--taxon', help='Taxon ID or URL', callback=strip_url)
@click.option('-x', '--create-xmp', is_flag=True,
              help="Create XMP sidecar file if it doesn't already exist")
@click.argument('images', nargs=-1, type=GlobPath(), callback=chain_lists)
# @click.argument('images', nargs=-1, type=click.Path(dir_okay=False, exists=True, writable=True))
def tag(ctx, observation, taxon, common_names, hierarchical, create_xmp, images):
    """
    Get taxonomy tags from an iNaturalist observation or taxon, and write them to local image
    metadata.

    \b
    ### Data Sources
    Either a taxon or observation may be specified, either by ID or URL.
    For example, all of the following options will fetch the same taxonomy
    metadata:
    ```
    -t 48978
    -t https://www.inaturalist.org/taxa/48978-Dirona-picta
    -o 45524803
    -o https://www.inaturalist.org/observations/45524803
    ```

    \b
    The difference is that specifying a taxon (`-t`) will fetch only taxonomy
    metadata, while specifying an observation (`-o`) will fetch taxonomy plus
    observation metadata.

    \b
    ### Images
    Multiple paths are supported, as well as glob patterns, for example:
    `0001.jpg IMG*.jpg ~/observations/**.jpg`
    If no images are specified, the generated keywords will be printed.

    \b
    ### Keywords
    Keywords will be generated in the format:
    `taxonomy:{rank}={name}`

    \b
    ### DarwinCore
    If an observation is specified, DwC metadata will also be generated, in the
    form of XMP tags. Among other things, this includes taxonomy tags in the
    format:
    `dwc:{rank}="{name}"`

    \b
    ### Sidecar Files
    By default, XMP tags will be written to a sidecar file if it already exists.
    Use the `-x` option to create a new one if it doesn't exist.

    \b
    ### Hierarchical Keywords
    If specified (`-h`), hierarchical keywords will be generated. These will be
    interpreted as a tree structure by image viewers that support them.

    \b
    For example, the following keywords:
    ```
    Animalia
    Animalia|Arthropoda
    Animalia|Arthropoda|Chelicerata
    Animalia|Arthropoda|Hexapoda
    ```

    \b
    Will translate into the following tree structure:
    ```
    Animalia
        ┗━Arthropoda
            ┣━Chelicerata
            ┗━Hexapoda
    ```
    #
    """
    if not any([observation, taxon]):
        click.echo(ctx.get_help())
        ctx.exit()
    if all([observation, taxon]):
        click.secho('Provide either a taxon or an observation', fg='red')
        ctx.exit()

    keywords = get_keywords(
        observation_id=observation,
        taxon_id=taxon,
        common=common_names,
        hierarchical=hierarchical,
    )
    metadata = get_keyword_metadata(keywords)

    if observation and images:
        metadata.update(get_observation_dwc_terms(observation))
    for image in images:
        write_metadata(image, metadata, create_xmp=create_xmp)

    # If no images were specified, just print keywords
    if not images:
        click.echo('\n'.join(keywords))


# Main CLI entry point
main = tag
tag.help = colorize_help_text(tag.help)

# TesseractXplore 
[![Build Status](https://travis-ci.org/JWCook/naturtag.svg?branch=dev)](https://travis-ci.org/JKamlah/tesseractXplore)
![GitHub issues](https://itmg.shields.io/github/issues/JKamlah/tesseractXplore)

This tool provides a graphical interface to [tesseract](https://github.com/tesseract-ocr/tesseract). 
Images can be loaded via a file chooser window or via drag-and-drop. The result fulltext-files can also be edited.

# Contents

* [Use Cases](#use-cases)
* [Development Status](#development-status)
* [Python Package](#python-package)
* [GUI](#gui)
    * [Installation](#gui-installation)
    * [Usage](#gui-usage)
    * [Image Selection and Tagging](#image-selection-and-tagging)
    * [Model Search](#model-search)
    * [Saved Species](#saved-species)
    * [Metadata](#metadata)
    * [Settings](#settings)
    * [Keyboard Shortcuts](#keyboard-shortcuts)
* [See Also](#see-also)

## Use Cases
The purpose of this project is a simple application for user  

### Tesseract 
This can improve interoperability with other tools and systems that interact with biodiversity
data. For example, in addition to iNaturalist you may submit gts of certain species to
another biodiversity gt platform with a more specific focus, such as eBird, BugGuide, or
Mushroom Observer. For that use case, this tool supports
[Simple Darwin Core](https://dwc.tdwg.org/simple).

### Images 
This can also simplify tagging photos for photo hosting sites like Flickr. For that use case, this
tool generates keywords in the same format as
[iNaturalist's Flickr Tagger](https://www.inaturalist.org/taxa/flickr_tagger).

### Fulltext-fileformat 
Finally, this can enable you to search and filter your local photo collection by type of organism
like you can in the iNaturalist web UI or mobile apps. For that use case, a photo viewer or DAM
that supports **hierarchical keywords** is recommended, such as Lightroom,
[FastPictureViewer](https://www.fastpictureviewer.com), or
[XnViewMP](https://www.xnview.com/en/xnviewmp).

# Development Status
See [Issues](https://github.com/JKamlah/tesseract-xplore/issues?q=) for planned features and
current progress.

This is project is currently in an early development stage and not very polished. All the
features described below are functional, however.

# Python Package
See the wiki for details on the python package.

## Installation
OS-specific builds will be coming soon, but for now running it requires a local python development
environment. To install:
```
pip install naturtag[ui]
```
Some additional dependencies are required on Windows:
```
pip install naturtag[ui-win]
```

The standard text render has problems with combinded glyphs, 
to present them correctly you have to install pango2:


1. Install pangoft2 (`apt install libfreetype6-dev libpango1.0-dev
   libpangoft2-1.0-0`) or ensure it is available in pkg-config
2. Recompile kivy. Check that pangoft2 is found `use_pangoft2 = 1`
3. Test it! Enforce the text core renderer to pango using environment variable:
   `export KIVY_TEXT=pango`

 

##  GUI Usage

### Image Selection and Tagging
The basic UI components are shown below:
![Screenshot]

1. Drag & drop images or folders into the window.
2. Or, select files via the file browser on the right
3. Enter an iNaturalist gt ID or model ID
4. Click the 'Run' button in the lower-left to tag the selected images

Other things to do:
* **Middle-click** an image to remove it
* **Right-click** an image for a menu of more actions
* See [Metadata](#metadata) for more details

### Model Search
If you don't already know the model ID, click the 'Find a Species' button to go to the model
search screen. You can start with searching by name, with autocompletion support:

![Screenshot](assets/screenshots/gui-model-search.png)

You can also run a full search using the additional filters. For example, to search for plants
and fungi with 'goose' in either the species or genus name:

![Screenshot](assets/screenshots/gui-model-search-results.png)

### Saved Species
The additional tabs on the model screen contain:
* History of recently viewed taxa
* Most frequently viewed taxa
* Starred taxa

To save a particular model for future reference, click the ✩ icon in the top left of its info panel,
and it will be saved in the ★ tab. These items can be re-ordered via **Right-click** -> **Move to top**.
(Unfortunately, drag-and-drop functionality is not currently possible for list items).

### Metadata
**Right-click** an image and select **Copy Flickr tags** to copy keyword tags compatible with Flickr.
![Screenshot]

Also, a very simple (and ugly) metadata view is included, mainly for debugging purposes.
To open it, **Right-click** an image and select **View metadata**.

![Screenshot]

### Settings
There are also some settings to customize the metadata that your images will be tagged with,
as well as iNaturalist info used in search filters. And yes, there is a dark mode, because
why not.

![Screenshot]

See [CLI Usage](#cli-usage) for more details on these settings.

### Keyboard Shortcuts
Some keyboard shortcuts are included for convenience:

Key(s)          | Action                    | Screen
----            |----                       |----------
F11             | Toggle fullscreen         | All
Ctrl+O          | Open file chooser         | Image selection
Shift+Ctrl+O    | Open file chooser (dirs)  | Image selection
Ctrl+Enter      | Run image tagger          | Image selection
Ctrl+Enter      | Run model search          | Model search
Shift+Ctrl+X    | Clear selected images     | Image selection
Shift+Ctrl+X    | Clear search filters      | Model search
Ctrl+S          | Open settings screen      | All
Ctrl+Backspace  | Return to main screen     | All
Ctrl+Q          | Quit                      | All

# See Also
*  This project is based on [naturtag](https://github.com/JWCook/naturtag).


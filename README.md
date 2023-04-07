# Test report PDF

The goal of this tool is to generate asciidoc pdf which includes Junit .xml test
results.
This tool was mainly tested with cukinia generated Junit files.

## Usage

 $ ./compile.sh -h

A docker support is provided using [cqfd](https://github.com/savoirfairelinux/cqfd).
When building directly on the machine, asciidoctor-pdf and xmlstarlet are required.

## Features

Xml files are automatically detected and dispaled in the test report. Each file creates its own table with all tests one after another.
Several tables can be generated for the same file using cukinia suite feature : `logging suite "name"` in the cukinia configuration file. This will also change the title of the table.

To specify the table title for a machine, use the class feature of cukinia : `logging class "name"`. This will append "for name" in the title.

A Prerequisites part can be added on top of the document. It is written in asciidoc in the file `include/prerequisites.adoc`.
A Notes part can also be added at the end using the file `include/notes.adoc`.
Both files are optional and can be removed if they are not needed.

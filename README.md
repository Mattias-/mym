# mym

mym is a script-friendly build server that use docker.
The idea is simple:

 - Given a docker image and an input file an output file is created.
 - What the input and output files should contain is up to the user.

Examples for the input file:

  - Configuration file for a complex build process
  - Archive with source code
  - ...

The output file could contain:

  - Log of the build process
  - A binary
  - ...

Another input is a name of the docker image to use.

## Usage

Running a build is done by sending a POST request to
`/<image_name>/<output_file_name>`
With a request body containing url encoded form data:
`input=<input_file_bytes>`

Alternatively the image and output file name can be set with url encoded form
data:
`image=<image_name>&output=<output_file_name>&input=<input_file_bytes>`


## An example

```bash
curl --remote-name \
  --user admin:secret \
  --form input=@archive.zip \
  http://localhost/builder/output.pdf
```

alternatively:

```bash
curl --output output.pdf \
  --user admin:secret \
  --form input=@archive.zip \
  --form image=builder \
  --form output=output.pdf \
  http://localhost
```

What happens during the build process is the following:

0. A container is started using a docker image `builder`
1. `archive.zip` is placed in `/tmp/inputdir` in the container
2. The script `/tmp/build output.pdf` is executed
3. (The build script together with the input file creates the output file and
    place it at `/tmp/output.pdf`)
4. The file located at `/tmp/output.pdf` is sent as a response


## Configuration

Username, passwords and what docker images they can use are configured in
`config.yaml`.
Build timeout is configured in this file as well.


The docker images have some prerequisites:
There must be a script at `/tmp/build`



## Be safe

Make sure the image is not using the root account

## FYI

- Network is disabled on the container
- The `/tmp/inputdir` is a mounted read only directory.
- Having `WORKDIR` set to `/tmp` probably make things easier


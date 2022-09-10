# links-alive
Link validation engine based on beautifulsoup4

Usage:
`python links-alive.py [SITE_ADDRESS]`
Example:
`python links-alive.py "https://djfedos.github.io"`

**links-alive** outputs two files: `valid.log` and `invalid.log`, with valid and indvalid links respectively.
Not all the links in `invalid.log` are truly invalid, but it's worth checking them manually just in case.
All the links in `valid.log` at least have returned code 200 to the GET request.

import re

# Global configs
known_coord_vars = "longitude|latitude|lon|lat|projection_y_coordinate|projection_x_coordinate".split("|")
workdir = "/gws/pw/j07/ukcp18/ai-astephen"
outdir = f"{workdir}/outputs"
encdir = f"{workdir}/encodings"
tmpdir = f"{workdir}/tmpdir"
LATEST = "latest"

# Extract configs
batch_size = 1000
zpad = 5
regex_int = re.compile("^-?\d+$")

# Transform configs
columns = ["varid", "collection"]


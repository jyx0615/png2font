#!/usr/bin/env bash
set -euo pipefail

# Start the png2font FastAPI Server
echo "================================================================="
echo "  📦 Conda Environment: genFont"
echo "================================================================="

# Source Conda setup script to enable 'conda activate' inside subshells
if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
    source "/opt/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    # Fallback to conda's shell integration hook
    eval "$(conda shell.bash hook)"
fi

# Activate the conda environment correctly
conda activate genFont


# Usage: ./run.sh [PNG_FOLDER] [FONTNAME]
# Defaults: PNG_FOLDER=glyphs, FONTNAME from config.toml or MyCustomFont

PNG_FOLDER=${1:-glyphs}

# If a font name was provided as the second arg, use it; otherwise try config.toml
if [ "${2:-}" != "" ]; then
	FONTNAME="$2"
else
	FONTNAME=""
	if [ -f config.toml ]; then
		# Find the fontname under the [font] table. Trim spaces and quotes.
		FONTNAME=$(awk -F'=' '
			/^\[font\]/{in_font=1; next}
			in_font && $1 ~ /fontname/ {
				v=$2; gsub(/^[ \t]+|[ \t]+$/,"",v); gsub(/\"/,"",v); print v; exit
			}
		' config.toml)
	fi
	FONTNAME=${FONTNAME:-MyCustomFont}
fi

echo "Converting PNGs in '${PNG_FOLDER}' to SVGs..."
python3 png2svg.py --png_folder "${PNG_FOLDER}" --svg_output "svg_glyphs"

echo "Generating TTF from svg_glyphs with fontname='${FONTNAME}'..."
fontforge -script font.py svg_glyphs --fontname "${FONTNAME}" --fullname "${FONTNAME}" --familyname "${FONTNAME}"

echo "Embedding SVGs into ${FONTNAME}.ttf..."
addsvg svg_glyphs "${FONTNAME}.ttf"

echo "Done. Output: ${FONTNAME}.ttf"

cd nanoemoji
echo "Running nanoemoji to generate COLV1 font...(may take more than 10 minutes)"
maximum_color ../${FONTNAME}.ttf
cd ..

COLOR_TTF="build/Font.ttf"
if [ -f "nanoemoji/${COLOR_TTF}" ]; then
	cp "nanoemoji/${COLOR_TTF}" "${FONTNAME}.ttf"
	echo "Applied maximum_color output to ${FONTNAME}.ttf"
else
	echo "Warning: nanoemoji/${COLOR_TTF} not found; keeping non-color ${FONTNAME}.ttf"
fi

# Shrink a WOFF/WOFF2 in place: keep every codepoint (--unicodes="*") but drop
# the redundant color tables (SVG, sbix, CBDT/CBLC bitmaps, FFTM) so only
# COLRv1 remains.
subset_drop_unused_tables() {
	local font_path="$1"
	local flavor="$2"
	local subset_path="${font_path}.subset"
	if pyftsubset "${font_path}" \
		--unicodes="*" \
		--drop-tables=SVG,sbix,CBDT,CBLC,FFTM \
		--flavor="${flavor}" \
		--output-file="${subset_path}"; then
		mv "${subset_path}" "${font_path}"
	else
		echo "Warning: pyftsubset failed for ${font_path}; keeping unsubsetted file"
		rm -f "${subset_path}"
	fi
}

# Convert to WOFF and WOFF2 in parallel — both just read the same TTF and
# don't depend on each other, so there's no reason to serialize them.
echo "Converting ${FONTNAME}.ttf to WOFF and WOFF2..."

(
	ttf2woff "${FONTNAME}.ttf" "${FONTNAME}.woff" \
		&& subset_drop_unused_tables "${FONTNAME}.woff" woff
) &
woff_pid=$!

(
	ttf2woff2 < "${FONTNAME}.ttf" > "${FONTNAME}.woff2" \
		&& subset_drop_unused_tables "${FONTNAME}.woff2" woff2
) &
woff2_pid=$!

wait "$woff_pid" "$woff2_pid"

echo "Done. Output: ${FONTNAME}.ttf, ${FONTNAME}.woff, ${FONTNAME}.woff2"
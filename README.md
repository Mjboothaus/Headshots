# Headshot Generator

This Streamlit application generates professional headshots from uploaded images (e.g., PNG, JPG) using OpenCV for face detection and PIL for image processing. It provides an interactive interface to adjust cropping, padding, zooming, and shifting, with real-time previews and annotations.

## Features
- **Upload and Process**: Upload a PNG or JPG image and generate a headshot with customisable settings.
- **Real-Time Adjustments**: Use sliders to adjust target size, padding ratios, shift (X/Y), zoom-out factor, and border color, with immediate updates to the processed image.
- **Side-by-Side Preview**: View "Before" (original) and "After" (processed) images side by side.
- **Annotations**: Toggle overlays for face box, padding areas, and final saved area (visible only in preview).
- **Undo**: Revert up to 5 previous states.
- **Auto Headshot**: Reset to default settings from `config.toml` and process from the original image.
- **Download**: Save an annotation-free headshot as `headshot.jpg`.

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Mjboothaus/Headshots.git
   cd Headshots
   ```
2. **Set Up Virtual Environment and Install Dependencies**:
   ```bash
   uv sync
   ```
   This will create a virtual environment and install all dependencies from `pyproject.toml` automatically.
3. **Run the App**:
   ```bash
   uv run streamlit run headshot_app.py
   ```
6. **Access the App**: Open the URL (e.g., `http://localhost:8501`) in your browser.

## Usage
1. **Upload Image**: Select an image via the file uploader. Defaults from `config.toml` are applied ($400 \times 500$, $20\%$ top padding, $50\%$ bottom, $10\%$ sides, $10\%$ zoom-out).
2. **Adjust Settings**:
   - **Target Width/Height**: Set output size (default: $400 \times 500$ pixels).
   - **Top/Bottom/Side Padding Ratio**: Adjust framing (defaults: $0.2$, $0.5$, $0.1$).
   - **Shift X/Y**: Move crop left/right or up/down (default: $0$ pixels).
   - **Zoom Out Factor**: Scale crop size (default: $1.1$ for $10\%$ zoom-out).
   - **Border Colour**: Choose border colour (default: black).
   - Hover over controls for tooltips.
3. **Auto Headshot**: Click to reset to `config.toml` defaults and process from the original image.
4. **Annotations**: Check "Show Annotations on Preview" to see face box (green), padding areas (blue/red/yellow), and final saved area (white).
5. **Undo**: Revert to previous states (up to 5).
6. **Download**: Save the processed headshot as `headshot.jpg` (annotation-free).

## Configuration
Settings are defined in `config.toml`:
- **[default]**: Default values for sliders (e.g., `target_width = 400`, `zoom_out_factor = 1.1`).
- **[slider]**: Min/max ranges for sliders (e.g., `zoom_out_min = 1.0`, `zoom_out_max = 1.5`).

## Mathematical Explanation of Transforms
The app applies a series of transformations to generate a headshot. Below are the mathematical details for each step:

### 1. Face Detection
- **Method**: OpenCV’s Haar Cascade classifier detects the face, returning a bounding box $(x, y, w, h)$, where:
  - $(x, y)$: Top-left corner of the face in the original image (pixels).
  - $w, h$: Face width and height (pixels).
- If no face is detected, a center crop is used based on the target aspect ratio.

### 2. Padding
Padding is added around the face based on ratios relative to face dimensions:
- Top padding: $p_t = h \cdot r_t$, where $r_t$ is the top padding ratio (e.g., $0.2$).
- Bottom padding: $p_b = h \cdot r_b$, where $r_b$ is the bottom padding ratio (e.g., $0.5$).
- Side padding (per side): $p_s = w \cdot r_s$, where $r_s$ is the side padding ratio (e.g., $0.1$).

### 3. Zoom-Out
The crop box is scaled by a zoom-out factor $z$ (e.g., $1.1$ for $10\%$ zoom-out):
- Crop width: $w_c = (w + 2 \cdot p_s) \cdot z$.
- Crop height: $h_c = (h + p_t + p_b) \cdot z$.

### 4. Shifting
The crop box center is offset by shifts $s_x, s_y$ (in pixels):
- Crop left: $x_c = \max(0, x + \frac{w}{2} - \frac{w_c}{2} + s_x)$.
- Crop top: $y_c = \max(0, y + \frac{h}{2} - \frac{h_c}{2} + s_y)$.
- Crop right: $x_r = \min(\text{image width}, x_c + w_c)$.
- Crop bottom: $y_b = \min(\text{image height}, y_c + h_c)$.
- Boundaries are adjusted to stay within the image:
  - If $x_r > \text{image width}$, set $x_c = x_c - (x_r - \text{image width})$, $x_r = \text{image width}$.
  - If $y_b > \text{image height}$, set $y_c = y_c - (y_b - \text{image height})$, $y_b = \text{image height}$.
  - If $x_c < 0$, set $x_r = x_r - x_c$, $x_c = 0$.
  - If $y_c < 0$, set $y_b = y_b - y_c$, $y_c = 0$.

### 5. Aspect Ratio Preservation
The crop is adjusted to match the target aspect ratio $r = \frac{w_t}{h_t}$, where $w_t, h_t$ are target width and height:
- If $\frac{w_c}{h_c} > r$:
  - New height: $h_c' = \frac{w_c}{r}$.
  - Update: $y_c' = \max(0, y_c - \frac{h_c' - h_c}{2})$, $y_b' = \min(\text{image height}, y_c' + h_c')$.
- If $\frac{w_c}{h_c} \leq r$:
  - New width: $w_c' = h_c \cdot r$.
  - Update: $x_c' = \max(0, x_c - \frac{w_c' - w_c}{2})$, $x_r' = \min(\text{image width}, x_c' + w_c')$.

### 6. Resizing and Borders
- The cropped image is scaled to fit within $w_t \times h_t$ using `thumbnail` (preserving aspect ratio).
- Borders are added to match the exact target size:
  - Border width: $\frac{w_t - w_{\text{cropped}}}{2}$.
  - Border height: $\frac{h_t - h_{\text{cropped}}}{2}$.
- The final image is resized to $w_t \times h_t$ using Lanczos interpolation.

### 7. Annotations (Optional)
- Face box, padding areas, and final saved area are drawn on the preview (scaled to final image coordinates).
- Scaling factors: $s_x = \frac{w_{\text{final}}}{x_r - x_c}$, $s_y = \frac{h_{\text{final}}}{y_b - y_c}$.
- Coordinates are adjusted (e.g., face box: $(s_x \cdot (x - x_c), s_y \cdot (y - y_c))$).

## Troubleshooting
- **Image Not Updating**: If sliders (e.g., zoom-out) don’t update the "After" image, check `key` parameters in `headshot_app.py` and ensure `config.toml` is present. Upload the image for debugging.
- **Face Detection Issues**: If "No face detected" appears, adjust `scaleFactor` (e.g., $1.05$) or `minNeighbors` (e.g., $3$) in `headshot_app.py` (line 62). Upload the image for specific tweaks.
- **Dependencies**: Add new packages if needed:
  ```bash
  uv add package-name
  ```
  Or sync existing dependencies:
  ```bash
  uv sync
  ```
- **Python Version**: Python 3.13 should work, but if issues arise, try Python 3.11:
  ```bash
  uv venv --python 3.11
  uv sync
  ```

## Notes
- Tested with Python 3.13 on macOS in Warp.
- Example images can be placed in the `images/` directory.
- For further customisation (e.g., reset button, custom annotations), modify `headshot_app.py` or `config.toml` and share requirements.

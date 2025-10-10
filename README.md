# Headshot Creator

A professional Streamlit application that transforms portrait photos into polished headshots using advanced OpenCV face detection and PIL image processing. The app features a modular architecture with intelligent caching, CAPTCHA verification, and extensive customisation options.

## ✨ Key Features

### 🔐 Security & Access
- **CAPTCHA Verification**: Math-based CAPTCHA system with randomised button positions to prevent automated access
- **Skip Protection**: Limited attempts with progressive difficulty

### 🎨 Profile-Based Processing
- **Corporate Profile**: Professional headshots with conservative cropping and styling
- **Creative Profile**: Artistic headshots with flexible framing options
- **Custom Profile**: Fully customisable parameters for specific requirements
- **Alphabetised Dropdown**: Easy profile selection with clear descriptions

### 🖼️ Advanced Image Processing
- **Smart Face Detection**: OpenCV-powered face detection with fallback center cropping
- **Real-Time Adjustments**: Live preview updates as you modify settings
- **Aspect Ratio Preservation**: Maintains image quality without stretching
- **Intelligent Borders**: Automatic border addition to match target dimensions

### 💾 Output & Export Options
- **Multiple Formats**: JPG, PNG, WEBP with quality settings
- **Editable Filenames**: Customise output filename with format-specific extensions
- **Download Options**: Annotation-free final images
- **Caching System**: MD5-based caching prevents unnecessary reprocessing

### 🎛️ Interactive Controls
- **Side-by-Side Preview**: Before/after comparison with zoom and pan
- **Segmented Controls**: Intuitive format selection interface
- **Smart Sliders**: Contextual controls with helpful tooltips
- **Undo System**: Revert to previous processing states (up to 5 levels)
- **Visual Annotations**: Toggle overlays for face detection, padding areas, and crop boundaries

## 🚀 Quick Start

### Prerequisites
- Python 3.13+ (tested with Python 3.13 on macOS)
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Mjboothaus/Headshots.git
   cd Headshots
   ```

2. **Install Dependencies**:
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Run the Application**:
   ```bash
   # Using uv
   uv run streamlit run headshot_app.py
   
   # Or using python directly
   python headshot_app.py
   
   # Or using streamlit directly
   streamlit run headshot_app.py
   ```

4. **Access the App**: Open your browser to `http://localhost:8501`

### Development Setup
For development with auto-reload:
```bash
uv run streamlit run headshot_app.py --server.runOnSave true
```

## 📚 Usage Guide

### Step 1: Verification
Upon first access, solve the CAPTCHA math problem and click the correct "Submit" button (positions randomised for security).

### Step 2: Upload Your Image
- Drag and drop or browse to select a portrait image (PNG, JPG, JPEG, WEBP)
- The app automatically applies face detection and default settings
- Supports images up to 200MB with helpful file size warnings

### Step 3: Choose Your Profile
Select from the dropdown menu:
- **Corporate**: Professional headshots (400×500px, conservative cropping)
- **Creative**: Artistic headshots (500×600px, flexible framing) 
- **LinkedIn**: Social media optimised (400×400px square)
- **Website**: Web-ready format (300×400px)
- **Custom**: Full manual control over all parameters

### Step 4: Customise Settings
**Output Format & Filename**:
- Choose format: JPG, PNG, or WEBP using segmented controls
- Edit filename with automatic extension updates
- Adjust quality settings for JPG/WEBP formats

**Image Adjustments** (visible with Custom profile or manual overrides):
- **Target Dimensions**: Set exact output width and height
- **Padding Ratios**: Adjust space around face (top, bottom, sides)
- **Shift Controls**: Move crop area horizontally and vertically
- **Zoom Factor**: Scale the crop area (1.0 = exact face size)
- **Border Colour**: Choose background colour for added borders

### Step 5: Preview & Refine
- **Side-by-Side View**: Compare original and processed images
- **Live Updates**: Changes reflect immediately with intelligent caching
- **Annotations**: Toggle overlays to see face detection and crop areas
- **Zoom & Pan**: Examine details in the preview images

### Step 6: Download
- Click "Download" to save your headshot
- Files saved with custom names and selected format
- Processing cached to avoid regeneration on repeated downloads

### Additional Features
- **Undo System**: Revert to previous states (up to 5 levels)
- **Auto Headshot**: Quick reset to profile defaults
- **Smart Caching**: Prevents reprocessing identical settings
- **Responsive Design**: Works on desktop and tablet devices

## ⚙️ Configuration

### Application Settings (`config.toml`)
The app uses a comprehensive TOML configuration file with the following sections:

**UI Configuration**:
- `[ui]`: Application title, warnings, labels, and help text
- `[ui.profiles]`: Profile descriptions and display names
- `[ui.formats]`: Output format options and quality settings

**Processing Defaults**:
- `[profiles.corporate]`, `[profiles.creative]`, etc.: Profile-specific parameters
- `[profiles.custom]`: Default values for custom profile

**Slider Ranges**:
- `[slider_config]`: Min/max values and step sizes for all sliders
- `[quality_config]`: Quality settings for different output formats

**System Settings**:
- `[system]`: Logging levels, cache settings, file size limits

### Example Profile Configuration
```toml
[profiles.corporate]
target_width = 400
target_height = 500
top_padding_ratio = 0.2
bottom_padding_ratio = 0.5
side_padding_ratio = 0.1
zoom_out_factor = 1.1
border_color = "black"
```

## 🏠 Technical Architecture

### Project Structure
```
src/headshot_generator/
├── __init__.py              # Package entry point
├── captcha.py               # CAPTCHA verification system
├── constants.py             # Application constants
├── models/                  # Data models
│   ├── image_data.py        # Image data structures
│   └── session_state.py     # Session state management
├── processing/              # Image processing logic
│   └── headshot_processor.py # Core processing algorithms
├── ui/                      # User interface components
│   ├── app.py               # Main application UI
│   └── sidebar.py           # Sidebar controls
└── utils/                   # Utilities and helpers
    ├── config.py            # Configuration management
    ├── exceptions.py        # Custom exceptions
    └── logger.py            # Logging utilities
```

### Key Components

**HeadshotApp** (`ui/app.py`): Main application controller that coordinates all components

**HeadshotProcessor** (`processing/headshot_processor.py`): Core image processing with OpenCV integration

**StreamlitCaptcha** (`captcha.py`): Security verification with math problems and UI tricks

**ConfigManager** (`utils/config.py`): Centralised configuration loading and validation

**ImageData & SessionStateManager** (`models/`): Data structures for image handling and session management

## 🔢 Image Processing Mathematics

The application applies a sophisticated series of transformations to generate professional headshots. Below are the mathematical details:

### 1. Face Detection
**Method**: OpenCV Haar Cascade classifier detects faces, returning bounding boxes $(x, y, w, h)$:
- $(x, y)$: Top-left corner coordinates (pixels)
- $(w, h)$: Face width and height (pixels)
- **Fallback**: If no faces detected, uses centre-crop based on target aspect ratio

### 2. Padding Calculation
Padding is applied around the detected face using configurable ratios:
- Top padding: $p_t = \lfloor h \cdot r_t \rfloor$
- Bottom padding: $p_b = \lfloor h \cdot r_b \rfloor$
- Side padding (each side): $p_s = \lfloor w \cdot r_s \rfloor$

Where $r_t, r_b, r_s$ are the top, bottom, and side padding ratios.

### 3. Zoom Factor Application
The crop dimensions are scaled by zoom-out factor $z$:
- Initial crop width: $w_{crop} = \lfloor (w + 2p_s) \cdot z \rfloor$
- Initial crop height: $h_{crop} = \lfloor (h + p_t + p_b) \cdot z \rfloor$

### 4. Crop Positioning with Shifts
Crop centre is calculated from face centre with user-defined shifts:
- Crop left: $x_{left} = x + \frac{w}{2} - \frac{w_{crop}}{2} + s_x$
- Crop top: $y_{top} = y + \frac{h}{2} - \frac{h_{crop}}{2} + s_y$
- Crop bounds: $(x_{left}, y_{top}, x_{left} + w_{crop}, y_{top} + h_{crop})$

Where $s_x, s_y$ are horizontal and vertical shift values.

### 5. Boundary Constraints
Crop bounds are constrained to image dimensions using boundary adjustment:
```
if left < 0: right ← right - left, left ← 0
if top < 0: bottom ← bottom - top, top ← 0  
if right > W: left ← left - (right - W), right ← W
if bottom > H: top ← top - (bottom - H), bottom ← H
```

### 6. Aspect Ratio Adjustment
Crop is adjusted to match target aspect ratio $r = \frac{w_t}{h_t}$:

**If crop is too wide** ($\frac{w_{crop}}{h_{crop}} > r$):
- New height: $h_{new} = \lfloor \frac{w_{crop}}{r} \rfloor$
- Adjust vertical position: $y_{top} \leftarrow \max(0, y_{top} - \frac{h_{new} - h_{crop}}{2})$

**If crop is too tall** ($\frac{w_{crop}}{h_{crop}} \leq r$):
- New width: $w_{new} = \lfloor h_{crop} \cdot r \rfloor$  
- Adjust horizontal position: $x_{left} \leftarrow \max(0, x_{left} - \frac{w_{new} - w_{crop}}{2})$

### 7. Final Image Processing
**Aspect-Preserving Resize**:
- Scale factor: $s = \min(\frac{w_t}{w_{crop}}, \frac{h_t}{h_{crop}})$
- New dimensions: $(w_{new}, h_{new}) = (\lfloor w_{crop} \cdot s \rfloor, \lfloor h_{crop} \cdot s \rfloor)$
- **Interpolation**: Lanczos resampling for high quality

**Border Addition**:
- Create canvas of size $(w_t, h_t)$ with selected border colour
- Centre resized image: $(\frac{w_t - w_{new}}{2}, \frac{h_t - h_{new}}{2})$
- **Result**: Final image exactly $(w_t, h_t)$ pixels with preserved aspect ratio

### 8. Caching & Optimization
**Cache Key Generation**: MD5 hash of processing parameters:
```
hash = MD5(target_size + padding_ratios + shifts + zoom + border_color)
```
- **Cache Hit**: Return cached result without reprocessing
- **Cache Miss**: Process image and store result with computed hash key

## 🔧 Troubleshooting

### Common Issues

**🔄 UI Not Updating / Caching Issues**:
- Clear browser cache and refresh (`Ctrl+F5` / `Cmd+Shift+R`)
- Check `logs/` directory for error messages
- Ensure `config.toml` is present and properly formatted
- Restart the application if session state becomes corrupted

**🎭 CAPTCHA Problems**:
- If CAPTCHA appears repeatedly, clear browser cookies for localhost
- Math problems use integer arithmetic - check for decimal inputs
- Button positions are randomised - look for "Submit" vs "Cancel" labels

**🔎 Face Detection Issues**:
- **"No face detected"**: The system falls back to centre crop automatically
- **Poor detection**: Ensure good lighting and face is clearly visible
- **Multiple faces**: System uses the largest detected face
- Adjust detection parameters in `src/headshot_generator/constants.py`:
  ```python
  DEFAULT_FACE_DETECTION_PARAMS = {
      "scaleFactor": 1.1,    # Try 1.05 for more sensitive detection
      "minNeighbors": 5,     # Try 3-7 for different sensitivity
      "minSize": (30, 30)    # Minimum face size
  }
  ```

**💾 File Processing Errors**:
- **Large files**: App supports up to 200MB but processing may be slow
- **Unsupported formats**: Convert to JPG, PNG, or WEBP
- **Memory errors**: Restart application or reduce image size
- **Permission errors**: Check file system permissions in upload directory

**🚀 Performance Issues**:
- **Slow processing**: Large images take longer - consider resizing input
- **Cache not working**: Check session state persistence and file permissions
- **High memory usage**: Restart application periodically during heavy use

### Development & Dependencies

**Package Management**:
```bash
# Add new dependencies
uv add package-name

# Update existing packages  
uv sync --upgrade

# Reinstall from scratch
rm -rf .venv uv.lock
uv sync
```

**Python Version Issues**:
```bash
# Recommended: Python 3.13
uv python install 3.13
uv venv --python 3.13

# Fallback: Python 3.11 if 3.13 has issues
uv venv --python 3.11
uv sync
```

**Configuration Debugging**:
```bash
# Validate config.toml syntax
python -c "import toml; print('Config valid:', toml.load('config.toml'))"

# Check package installation
uv run python -c "from headshot_generator import HeadshotApp; print('Import successful')"

# View detailed logs
tail -f logs/headshot_generator.log
```

### Getting Help

**Log Files**: Check `logs/headshot_generator.log` for detailed error information

**System Requirements**: 
- Python 3.13+ (3.11+ supported)
- 4GB+ RAM recommended
- OpenCV-compatible system (headless version used)

**Reporting Issues**: Include log files, `config.toml`, and system information when reporting problems

---

## 📝 Notes

- **Tested Environment**: Python 3.13 on macOS using Warp terminal
- **Sample Images**: Place test images in `images/` directory for development
- **Browser Compatibility**: Tested with Chrome, Firefox, Safari, Edge
- **Mobile Support**: Responsive design works on tablets, limited phone support
- **Docker Deployment**: See `Dockerfile` and `DEPLOY.md` for containerisation
- **Custom Profiles**: Edit `config.toml` to create new processing profiles

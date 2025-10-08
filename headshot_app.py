import streamlit as st
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFont, UnidentifiedImageError
import io
import toml

# Load config from TOML file
CONFIG = toml.load("config.toml")

class HeadshotProcessor:
    """Process images into headshots using OpenCV for face detection."""
    
    def __init__(
        self,
        input_image: Image.Image,
        target_width: int,
        target_height: int,
        padding_top_ratio: float,
        padding_bottom_ratio: float,
        padding_side_ratio: float,
        border_color: str,
        zoom_out_factor: float = 1.1,
        shift_x: int = 0,
        shift_y: int = 0,
        cascade_path: Optional[str] = None,
    ):
        self.input_image = input_image
        self.target_size = (target_width, target_height)
        self.padding_ratios = {
            "top": padding_top_ratio,
            "bottom": padding_bottom_ratio,
            "side": padding_side_ratio,
        }
        self.cascade_path = cascade_path or cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.border_color = border_color
        self.zoom_out_factor = zoom_out_factor
        self.shift_x = shift_x
        self.shift_y = shift_y
        self._validate_inputs()
    
    def _validate_inputs(self) -> None:
        if not Path(self.cascade_path).exists():
            raise FileNotFoundError(f"Haar Cascade file not found: {self.cascade_path}")
        if not isinstance(self.input_image, Image.Image):
            raise ValueError("Input must be a PIL Image object")
    
    def process_image(self) -> Image.Image:
        """Process image: detect face, crop with zoom-out and shift, resize with aspect ratio preservation."""
        try:
            img_array = np.array(self.input_image)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(self.cascade_path)
            faces = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                st.warning("No face detected. Using center crop.")
                width, height = self.input_image.size
                target_ratio = self.target_size[0] / self.target_size[1]
                # Apply zoom_out_factor to center crop as well
                base_crop_width = min(width, int(height * target_ratio))
                base_crop_height = min(height, int(width / target_ratio))
                crop_width = int(base_crop_width * self.zoom_out_factor)
                crop_height = int(base_crop_height * self.zoom_out_factor)
                crop_left = (width - crop_width) // 2 + self.shift_x
                crop_top = (height - crop_height) // 2 + self.shift_y
                crop_right = crop_left + crop_width
                crop_bottom = crop_top + crop_height
                
                if crop_left < 0:
                    crop_right -= crop_left
                    crop_left = 0
                if crop_top < 0:
                    crop_bottom -= crop_top
                    crop_top = 0
                if crop_right > width:
                    crop_left -= (crop_right - width)
                    crop_right = width
                if crop_bottom > height:
                    crop_top -= (crop_bottom - height)
                    crop_bottom = height
                
                cropped = self.input_image.crop((crop_left, crop_top, crop_right, crop_bottom))
                face_box = None
            else:
                x, y, w, h = faces[0]
                padding_top = int(h * self.padding_ratios["top"])
                padding_bottom = int(h * self.padding_ratios["bottom"])
                padding_side = int(w * self.padding_ratios["side"])
                
                crop_width = int((w + 2 * padding_side) * self.zoom_out_factor)
                crop_height = int((h + padding_top + padding_bottom) * self.zoom_out_factor)
                
                crop_left = max(0, x + w//2 - crop_width//2 + self.shift_x)
                crop_right = min(img_cv.shape[1], crop_left + crop_width)
                crop_top = max(0, y + h//2 - crop_height//2 + self.shift_y)
                crop_bottom = min(img_cv.shape[0], crop_top + crop_height)
                
                if crop_right > img_cv.shape[1]:
                    crop_left -= (crop_right - img_cv.shape[1])
                    crop_right = img_cv.shape[1]
                if crop_bottom > img_cv.shape[0]:
                    crop_top -= (crop_bottom - img_cv.shape[0])
                    crop_bottom = img_cv.shape[0]
                if crop_left < 0:
                    crop_right -= crop_left
                    crop_left = 0
                if crop_top < 0:
                    crop_bottom -= crop_top
                    crop_top = 0
                
                crop_width = crop_right - crop_left
                crop_height = crop_bottom - crop_top
                target_ratio = self.target_size[0] / self.target_size[1]
                if crop_width / crop_height > target_ratio:
                    new_height = int(crop_width / target_ratio)
                    crop_top = max(0, crop_top - (new_height - crop_height) // 2)
                    crop_bottom = min(img_cv.shape[0], crop_top + new_height)
                else:
                    new_width = int(crop_height * target_ratio)
                    crop_left = max(0, crop_left - (new_width - crop_width) // 2)
                    crop_right = min(img_cv.shape[1], crop_left + new_width)
                
                cropped = self.input_image.crop((crop_left, crop_top, crop_right, crop_bottom))
                face_box = (x, y, w, h)
            
            cropped.thumbnail(self.target_size, Image.LANCZOS)
            final_img = ImageOps.expand(
                cropped,
                border=(
                    (self.target_size[0] - cropped.width) // 2,
                    (self.target_size[1] - cropped.height) // 2
                ),
                fill=self.border_color
            )
            final_img = final_img.resize(self.target_size, Image.LANCZOS)
            
            # Annotations removed for cleaner UI
            
            return final_img
        
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return self.input_image

def main():
    # Set sidebar to be expanded by default
    st.set_page_config(
        page_title="Headshot Generator",
        page_icon="📸", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("Interactive Headshot Generator")
    st.write("Upload an image and adjust settings to generate a headshot with real-time preview.")
    
    # Initialize session state
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    if "original_image" not in st.session_state:
        st.session_state.original_image = None
    if "control_state" not in st.session_state:
        st.session_state.control_state = {
            "target_width": CONFIG["default"]["target_width"],
            "target_height": CONFIG["default"]["target_height"],
            "padding_top": CONFIG["default"]["padding_top"],
            "padding_bottom": CONFIG["default"]["padding_bottom"],
            "padding_side": CONFIG["default"]["padding_side"],
            "shift_x": CONFIG["default"]["shift_x"],
            "shift_y": CONFIG["default"]["shift_y"],
            "zoom_out_factor": CONFIG["default"]["zoom_out_factor"],
            "border_color": CONFIG["default"]["border_color"],
        }
    if "show_instructions" not in st.session_state:
        st.session_state.show_instructions = False
    
    # File uploader and profile selector in main area
    uploaded_file = st.file_uploader(
        "Choose an image to get started",
        type=["png", "jpg", "jpeg"],
        help="Upload a PNG or JPG image to process into a headshot."
    )
    
    # Profile selector in main area
    st.markdown("### 📋 Choose Profile or Custom Settings")
    
    # Get preset options from config (exclude 'slider' section)
    available_presets = [key.title() for key in CONFIG.keys() if key != 'slider' and key != 'download_formats']
    preset_options = available_presets + ["Custom"]
    
    # Initialize last_preset if not exists
    if "last_preset" not in st.session_state:
        st.session_state.last_preset = available_presets[0]  # Default to first preset
    
    selected_preset = st.selectbox(
        "Profile Configuration",
        preset_options,
        index=preset_options.index(st.session_state.last_preset) if st.session_state.last_preset in preset_options else 0,
        help="Choose a preset profile or select 'Custom' to manually adjust all settings in the sidebar"
    )
    
    # SIDEBAR CONTROLS
    st.sidebar.title("Controls")
    
    if uploaded_file is not None:
        try:
            input_image = Image.open(uploaded_file).convert("RGB")
            st.session_state.original_image = input_image
            st.session_state.current_image = input_image
            
            # Apply current settings on upload (preserve selected preset)
            processor = HeadshotProcessor(
                input_image=st.session_state.current_image,
                target_width=st.session_state.control_state["target_width"],
                target_height=st.session_state.control_state["target_height"],
                padding_top_ratio=st.session_state.control_state["padding_top"],
                padding_bottom_ratio=st.session_state.control_state["padding_bottom"],
                padding_side_ratio=st.session_state.control_state["padding_side"],
                border_color=st.session_state.control_state["border_color"],
                zoom_out_factor=st.session_state.control_state["zoom_out_factor"],
                shift_x=st.session_state.control_state["shift_x"],
                shift_y=st.session_state.control_state["shift_y"],
            )
            st.session_state.current_image = processor.process_image()
        except UnidentifiedImageError:
            st.error("Cannot identify image file. Please upload a valid PNG or JPG.")
            return
    
    # Sidebar controls header
    st.sidebar.subheader("🏛️ Manual Controls")
    st.sidebar.markdown("*Adjust individual settings*")
    
    # Function to apply preset settings
    def apply_preset(preset_name):
        preset_key = preset_name.lower()
        if preset_key in CONFIG and preset_key != 'slider':
            preset_config = CONFIG[preset_key]
            
            # Update session state with preset values
            st.session_state.control_state.update({
                "target_width": preset_config["target_width"],
                "target_height": preset_config["target_height"],
                "padding_top": preset_config["padding_top"],
                "padding_bottom": preset_config["padding_bottom"],
                "padding_side": preset_config["padding_side"],
                "shift_x": preset_config["shift_x"],
                "shift_y": preset_config["shift_y"],
                "zoom_out_factor": preset_config["zoom_out_factor"],
                "border_color": preset_config["border_color"],
            })
    
    # Check if preset changed and apply if not Custom
    if selected_preset != st.session_state.last_preset:
        st.session_state.last_preset = selected_preset
        if selected_preset != "Custom":
            apply_preset(selected_preset)
            # Also update the original image processing if we have one
            if st.session_state.original_image is not None:
                processor = HeadshotProcessor(
                    input_image=st.session_state.original_image,
                    target_width=st.session_state.control_state["target_width"],
                    target_height=st.session_state.control_state["target_height"],
                    padding_top_ratio=st.session_state.control_state["padding_top"],
                    padding_bottom_ratio=st.session_state.control_state["padding_bottom"],
                    padding_side_ratio=st.session_state.control_state["padding_side"],
                    border_color=st.session_state.control_state["border_color"],
                    zoom_out_factor=st.session_state.control_state["zoom_out_factor"],
                    shift_x=st.session_state.control_state["shift_x"],
                    shift_y=st.session_state.control_state["shift_y"],
                )
                st.session_state.current_image = processor.process_image()
            # Force rerun to update sliders with new values
            st.rerun()
    # Organize controls in sidebar with 2-column layout
    st.sidebar.subheader("Dimensions")
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            target_width = st.slider(
                "Width (px)",
                CONFIG["slider"]["target_width_min"],
                CONFIG["slider"]["target_width_max"],
                st.session_state.control_state["target_width"],
                10,
                help="Set the final width of the headshot in pixels.",
                key="target_width"
            )
        with col2:
            target_height = st.slider(
                "Height (px)",
                CONFIG["slider"]["target_height_min"],
                CONFIG["slider"]["target_height_max"],
                st.session_state.control_state["target_height"],
                10,
                help="Set the final height of the headshot in pixels.",
                key="target_height"
            )
    
    st.sidebar.subheader("Padding")
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            padding_top = st.slider(
                "Top Ratio",
                CONFIG["slider"]["padding_min"],
                CONFIG["slider"]["padding_top_max"],
                st.session_state.control_state["padding_top"],
                0.01,
                help="Add space above the face (as a fraction of face height) for headroom.",
                key="padding_top"
            )
            padding_bottom = st.slider(
                "Bottom Ratio",
                CONFIG["slider"]["padding_min"],
                CONFIG["slider"]["padding_bottom_max"],
                st.session_state.control_state["padding_bottom"],
                0.01,
                help="Add space below the face (as a fraction of face height) for shoulders.",
                key="padding_bottom"
            )
        with col2:
            padding_side = st.slider(
                "Side Ratio",
                CONFIG["slider"]["padding_min"],
                CONFIG["slider"]["padding_side_max"],
                st.session_state.control_state["padding_side"],
                0.01,
                help="Add space on the left and right of the face (as a fraction of face width).",
                key="padding_side"
            )
    
    st.sidebar.subheader("Position & Zoom")
    with st.sidebar:
        col1, col2 = st.columns(2)
        with col1:
            shift_x = st.slider(
                "Shift X (px)",
                CONFIG["slider"]["shift_min"],
                CONFIG["slider"]["shift_max"],
                st.session_state.control_state["shift_x"],
                5,
                help="Move the crop box left (negative) or right (positive) in pixels.",
                key="shift_x"
            )
            shift_y = st.slider(
                "Shift Y (px)",
                CONFIG["slider"]["shift_min"],
                CONFIG["slider"]["shift_max"],
                st.session_state.control_state["shift_y"],
                5,
                help="Move the crop box up (negative) or down (positive) in pixels.",
                key="shift_y"
            )
        with col2:
            zoom_out_factor = st.slider(
                "Zoom Factor",
                CONFIG["slider"]["zoom_out_min"],
                CONFIG["slider"]["zoom_out_max"],
                st.session_state.control_state["zoom_out_factor"],
                0.05,
                help="Scale the crop box size (1.0 = no zoom-out, 1.5 = 50% larger crop).",
                key="zoom_out_factor"
            )
    
    
    # Border color in sidebar
    st.sidebar.subheader("Appearance")
    border_color = st.sidebar.color_picker(
        "Border Colour",
        st.session_state.control_state["border_color"],
        help="Used when image doesn't match target aspect ratio",
        key="border_color"
    )
    
    # Process image in real-time
    if st.session_state.current_image is not None:
        # Check if any control has changed
        controls_changed = (
            target_width != st.session_state.control_state["target_width"] or
            target_height != st.session_state.control_state["target_height"] or
            padding_top != st.session_state.control_state["padding_top"] or
            padding_bottom != st.session_state.control_state["padding_bottom"] or
            padding_side != st.session_state.control_state["padding_side"] or
            shift_x != st.session_state.control_state["shift_x"] or
            shift_y != st.session_state.control_state["shift_y"] or
            zoom_out_factor != st.session_state.control_state["zoom_out_factor"] or
            border_color != st.session_state.control_state["border_color"]
        )
        
        if controls_changed:
            processor = HeadshotProcessor(
                input_image=st.session_state.original_image,
                target_width=target_width,
                target_height=target_height,
                padding_top_ratio=padding_top,
                padding_bottom_ratio=padding_bottom,
                padding_side_ratio=padding_side,
                border_color=border_color,
                zoom_out_factor=zoom_out_factor,
                shift_x=shift_x,
                shift_y=shift_y,
            )
            st.session_state.current_image = processor.process_image()
            st.session_state.control_state.update({
                "target_width": target_width,
                "target_height": target_height,
                "padding_top": padding_top,
                "padding_bottom": padding_bottom,
                "padding_side": padding_side,
                "shift_x": shift_x,
                "shift_y": shift_y,
                "zoom_out_factor": zoom_out_factor,
                "border_color": border_color,
            })
    
    
    # Display before and after images side by side with placeholders
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Image")
        if st.session_state.original_image is not None:
            st.image(st.session_state.original_image, caption="Before (Original)", width="stretch")
        else:
            placeholder = st.empty()
            placeholder.info("📷 Upload an image using the sidebar to get started")
    
    with col2:
        st.subheader("Processed Headshot")
        if st.session_state.current_image is not None:
            st.image(st.session_state.current_image, caption="After (Processed)", width="stretch")
        else:
            placeholder = st.empty()
            placeholder.info("✨ Your processed headshot will appear here")
    
    # Only show download section if we have processed images
    if st.session_state.current_image is not None and st.session_state.original_image is not None:
        st.markdown("---")
        
        # Download section with multiple format options from config
        processor = HeadshotProcessor(
            input_image=st.session_state.original_image,
            target_width=target_width,
            target_height=target_height,
            padding_top_ratio=padding_top,
            padding_bottom_ratio=padding_bottom,
            padding_side_ratio=padding_side,
            border_color=border_color,
            zoom_out_factor=zoom_out_factor,
            shift_x=shift_x,
            shift_y=shift_y,
        )
        clean_image = processor.process_image()
        
        st.subheader("💾 Download Headshot")
        
        # Load download formats from config
        formats = CONFIG.get("download_formats", {})
        if formats:
            # Create format selection with radio buttons
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Format:**")
                format_options = list(formats.keys())
                selected_format = st.radio(
                    "Choose format",
                    format_options,
                    index=0,
                    label_visibility="collapsed",
                    horizontal=True
                )
            
            with col2:
                # Generate download button for selected format
                format_info = formats[selected_format]
                buffer = io.BytesIO()
                save_kwargs = {"format": format_info["format"]}
                
                if format_info.get("quality"):
                    save_kwargs["quality"] = format_info["quality"]
                if format_info.get("optimize"):
                    save_kwargs["optimize"] = format_info["optimize"]
                    
                clean_image.save(buffer, **save_kwargs)
                
                st.download_button(
                    label=f"💾 Download as {format_info['format'].upper()}",
                    data=buffer.getvalue(),
                    file_name=f"headshot{format_info['extension']}",
                    mime=format_info["mime"],
                    help=f"Download the processed headshot as {format_info['format']} format",
                    width="stretch"
                )
        else:
            # Fallback to JPEG if no formats configured
            buffer = io.BytesIO()
            clean_image.save(buffer, format="JPEG")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="💾 Download Headshot",
                    data=buffer.getvalue(),
                    file_name="headshot.jpg",
                    mime="image/jpeg",
                    help="Download the processed headshot as a JPEG file",
                    width="stretch"
                )
    
    # Instructions toggle section
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        button_label = "📝 Show Instructions" if not st.session_state.show_instructions else "🔼 Hide Instructions"
        if st.button(button_label, key="instructions_toggle", use_container_width=True):
            st.session_state.show_instructions = not st.session_state.show_instructions
            st.rerun()
    
    # Display instructions if toggled on
    if st.session_state.show_instructions:
        st.markdown("")
        try:
            with open("instructions.md", "r", encoding="utf-8") as f:
                instructions_content = f.read()
            st.markdown(instructions_content)
        except FileNotFoundError:
            st.error("Instructions file not found. Please ensure instructions.md exists in the application directory.")

if __name__ == "__main__":
    main()

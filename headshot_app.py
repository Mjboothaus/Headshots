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
        annotate: bool = False,
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
        self.annotate = annotate
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
            
            if self.annotate:
                draw = ImageDraw.Draw(final_img)
                try:
                    font = ImageFont.truetype("arial.ttf", 14)
                except:
                    font = ImageFont.load_default()
                
                if face_box:
                    orig_width, orig_height = self.input_image.size
                    final_width, final_height = final_img.size
                    scale_x = final_width / (crop_right - crop_left)
                    scale_y = final_height / (crop_bottom - crop_top)
                    
                    x, y, w, h = face_box
                    scaled_x = int((x - crop_left) * scale_x)
                    scaled_y = int((y - crop_top) * scale_y)
                    scaled_w = int(w * scale_x)
                    scaled_h = int(h * scale_y)
                    
                    draw.rectangle(
                        (scaled_x, scaled_y, scaled_x + scaled_w, scaled_y + scaled_h),
                        outline="green",
                        width=2
                    )
                    draw.text(
                        (scaled_x, scaled_y - 15),
                        "Face",
                        fill="green",
                        font=font
                    )
                    
                    padding_top_px = int(h * self.padding_ratios["top"] * scale_y)
                    padding_bottom_px = int(h * self.padding_ratios["bottom"] * scale_y)
                    padding_side_px = int(w * self.padding_ratios["side"] * scale_x)
                    
                    draw.rectangle(
                        (0, 0, final_width, padding_top_px),
                        outline="blue",
                        width=1
                    )
                    draw.text(
                        (10, padding_top_px // 2),
                        "Top Padding",
                        fill="blue",
                        font=font
                    )
                    
                    draw.rectangle(
                        (0, final_height - padding_bottom_px, final_width, final_height),
                        outline="red",
                        width=1
                    )
                    draw.text(
                        (10, final_height - padding_bottom_px // 2),
                        "Bottom Padding",
                        fill="red",
                        font=font
                    )
                    
                    draw.rectangle(
                        (0, 0, padding_side_px, final_height),
                        outline="yellow",
                        width=1
                    )
                    draw.rectangle(
                        (final_width - padding_side_px, 0, final_width, final_height),
                        outline="yellow",
                        width=1
                    )
                    draw.text(
                        (padding_side_px // 2, final_height // 2),
                        "Side",
                        fill="yellow",
                        font=font
                    )
                
                draw.rectangle(
                    (2, 2, final_width - 3, final_height - 3),
                    outline="white",
                    width=3
                )
                draw.text(
                    (10, 10),
                    f"Final Saved Area: {self.target_size[0]}x{self.target_size[1]}",
                    fill="white",
                    font=font
                )
            
            return final_img
        
        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            return self.input_image

def main():
    st.title("Interactive Headshot Generator")
    st.write("Upload an image and adjust settings to generate a headshot with real-time preview.")
    
    st.subheader("Parameter Explanations")
    st.markdown("""
    - **Target Width/Height**: Final dimensions of the headshot in pixels. Shown as "Final Saved Area" (white rectangle) in the annotated preview.
    - **Top Padding Ratio**: Adds space above the face (fraction of face height) for headroom. Shown as a blue outline.
    - **Bottom Padding Ratio**: Adds space below the face for shoulders. Shown as a red outline.
    - **Side Padding Ratio**: Adds space on the left and right of the face. Shown as yellow outlines.
    - **Shift X/Y**: Moves the crop box left/right (X) or up/down (Y) in pixels. Positive X shifts right, positive Y shifts down.
    - **Zoom Out Factor**: Scales the crop box (1.0 = no zoom-out, 1.5 = 50% larger crop). Higher values include more of the image.
    - **Border Color**: Color of borders added to maintain the target aspect ratio.
    - **Show Annotations**: Toggles visual overlays (face box, padding areas, final saved area) on the preview. The downloaded image is annotation-free.
    - **Auto Headshot**: Resets to default settings from config.toml and processes the original image.
    """)
    
    # Initialize session state
    if "image_history" not in st.session_state:
        st.session_state.image_history = []
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
            "annotate": False,
        }
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image (e.g., PNG, JPG)",
        type=["png", "jpg", "jpeg"],
        help="Upload a PNG or JPG image to process into a headshot."
    )
    
    if uploaded_file is not None:
        try:
            input_image = Image.open(uploaded_file).convert("RGB")
            st.session_state.original_image = input_image
            st.session_state.current_image = input_image
            st.session_state.image_history = []  # Reset history on new upload
            # Apply default settings on upload
            processor = HeadshotProcessor(
                input_image=st.session_state.current_image,
                target_width=CONFIG["default"]["target_width"],
                target_height=CONFIG["default"]["target_height"],
                padding_top_ratio=CONFIG["default"]["padding_top"],
                padding_bottom_ratio=CONFIG["default"]["padding_bottom"],
                padding_side_ratio=CONFIG["default"]["padding_side"],
                border_color=CONFIG["default"]["border_color"],
                annotate=False,
                zoom_out_factor=CONFIG["default"]["zoom_out_factor"],
                shift_x=CONFIG["default"]["shift_x"],
                shift_y=CONFIG["default"]["shift_y"],
            )
            st.session_state.current_image = processor.process_image()
            st.session_state.control_state.update({
                "target_width": CONFIG["default"]["target_width"],
                "target_height": CONFIG["default"]["target_height"],
                "padding_top": CONFIG["default"]["padding_top"],
                "padding_bottom": CONFIG["default"]["padding_bottom"],
                "padding_side": CONFIG["default"]["padding_side"],
                "shift_x": CONFIG["default"]["shift_x"],
                "shift_y": CONFIG["default"]["shift_y"],
                "zoom_out_factor": CONFIG["default"]["zoom_out_factor"],
                "border_color": CONFIG["default"]["border_color"],
                "annotate": False,
            })
        except UnidentifiedImageError:
            st.error("Cannot identify image file. Please upload a valid PNG or JPG.")
            return
    
    # Settings
    st.subheader("Headshot Settings")
    col1, col2 = st.columns(2)
    with col1:
        target_width = st.slider(
            "Target Width (pixels)",
            CONFIG["slider"]["target_width_min"],
            CONFIG["slider"]["target_width_max"],
            st.session_state.control_state["target_width"],
            10,
            help="Set the final width of the headshot in pixels.",
            key="target_width"
        )
        target_height = st.slider(
            "Target Height (pixels)",
            CONFIG["slider"]["target_height_min"],
            CONFIG["slider"]["target_height_max"],
            st.session_state.control_state["target_height"],
            10,
            help="Set the final height of the headshot in pixels.",
            key="target_height"
        )
        padding_top = st.slider(
            "Top Padding Ratio",
            CONFIG["slider"]["padding_min"],
            CONFIG["slider"]["padding_top_max"],
            st.session_state.control_state["padding_top"],
            0.01,
            help="Add space above the face (as a fraction of face height) for headroom.",
            key="padding_top"
        )
        shift_x = st.slider(
            "Shift X (pixels)",
            CONFIG["slider"]["shift_min"],
            CONFIG["slider"]["shift_max"],
            st.session_state.control_state["shift_x"],
            5,
            help="Move the crop box left (negative) or right (positive) in pixels.",
            key="shift_x"
        )
    with col2:
        padding_bottom = st.slider(
            "Bottom Padding Ratio",
            CONFIG["slider"]["padding_min"],
            CONFIG["slider"]["padding_bottom_max"],
            st.session_state.control_state["padding_bottom"],
            0.01,
            help="Add space below the face (as a fraction of face height) for shoulders.",
            key="padding_bottom"
        )
        padding_side = st.slider(
            "Side Padding Ratio",
            CONFIG["slider"]["padding_min"],
            CONFIG["slider"]["padding_side_max"],
            st.session_state.control_state["padding_side"],
            0.01,
            help="Add space on the left and right of the face (as a fraction of face width).",
            key="padding_side"
        )
        shift_y = st.slider(
            "Shift Y (pixels)",
            CONFIG["slider"]["shift_min"],
            CONFIG["slider"]["shift_max"],
            st.session_state.control_state["shift_y"],
            5,
            help="Move the crop box up (negative) or down (positive) in pixels.",
            key="shift_y"
        )
        zoom_out_factor = st.slider(
            "Zoom Out Factor",
            CONFIG["slider"]["zoom_out_min"],
            CONFIG["slider"]["zoom_out_max"],
            st.session_state.control_state["zoom_out_factor"],
            0.05,
            help="Scale the crop box size (1.0 = no zoom-out, 1.5 = 50% larger crop).",
            key="zoom_out_factor"
        )
        border_color = st.color_picker(
            "Border Color",
            st.session_state.control_state["border_color"],
            help="Choose the color for borders added to maintain the target aspect ratio.",
            key="border_color"
        )
    
    # Annotation toggle
    annotate = st.checkbox(
        "Show Annotations on Preview",
        value=st.session_state.control_state["annotate"],
        help="Toggle visual overlays (face box, padding areas, final saved area) on the preview. The downloaded image is annotation-free.",
        key="annotate"
    )
    
    # Auto Headshot Button
    if st.button("Auto Headshot", help="Reset to default settings from config.toml and process the original image."):
        if st.session_state.original_image is not None:
            if len(st.session_state.image_history) >= 5:
                st.session_state.image_history.pop(0)
            st.session_state.image_history.append(st.session_state.current_image.copy())
            processor = HeadshotProcessor(
                input_image=st.session_state.original_image,
                target_width=CONFIG["default"]["target_width"],
                target_height=CONFIG["default"]["target_height"],
                padding_top_ratio=CONFIG["default"]["padding_top"],
                padding_bottom_ratio=CONFIG["default"]["padding_bottom"],
                padding_side_ratio=CONFIG["default"]["padding_side"],
                border_color=CONFIG["default"]["border_color"],
                annotate=annotate,
                zoom_out_factor=CONFIG["default"]["zoom_out_factor"],
                shift_x=CONFIG["default"]["shift_x"],
                shift_y=CONFIG["default"]["shift_y"],
            )
            st.session_state.current_image = processor.process_image()
            st.session_state.control_state.update({
                "target_width": CONFIG["default"]["target_width"],
                "target_height": CONFIG["default"]["target_height"],
                "padding_top": CONFIG["default"]["padding_top"],
                "padding_bottom": CONFIG["default"]["padding_bottom"],
                "padding_side": CONFIG["default"]["padding_side"],
                "shift_x": CONFIG["default"]["shift_x"],
                "shift_y": CONFIG["default"]["shift_y"],
                "zoom_out_factor": CONFIG["default"]["zoom_out_factor"],
                "border_color": CONFIG["default"]["border_color"],
                "annotate": annotate,
            })
    
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
            border_color != st.session_state.control_state["border_color"] or
            annotate != st.session_state.control_state["annotate"]
        )
        
        if controls_changed:
            if len(st.session_state.image_history) >= 5:
                st.session_state.image_history.pop(0)
            st.session_state.image_history.append(st.session_state.current_image.copy())
            processor = HeadshotProcessor(
                input_image=st.session_state.original_image,
                target_width=target_width,
                target_height=target_height,
                padding_top_ratio=padding_top,
                padding_bottom_ratio=padding_bottom,
                padding_side_ratio=padding_side,
                border_color=border_color,
                annotate=annotate,
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
                "annotate": annotate,
            })
    
    # Undo Button
    if st.button("Undo", help="Revert to the previous image state (up to 5 steps)."):
        if st.session_state.image_history:
            st.session_state.current_image = st.session_state.image_history.pop()
    
    # Display before and after images side by side
    if st.session_state.current_image is not None and st.session_state.original_image is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.image(st.session_state.original_image, caption="Before (Original)", width="stretch")
        with col2:
            st.image(st.session_state.current_image, caption="After (Processed Headshot)", width="stretch")
        
        # Download button (save without annotations)
        processor = HeadshotProcessor(
            input_image=st.session_state.original_image,
            target_width=target_width,
            target_height=target_height,
            padding_top_ratio=padding_top,
            padding_bottom_ratio=padding_bottom,
            padding_side_ratio=padding_side,
            border_color=border_color,
            annotate=False,
            zoom_out_factor=zoom_out_factor,
            shift_x=shift_x,
            shift_y=shift_y,
        )
        clean_image = processor.process_image()
        buffer = io.BytesIO()
        clean_image.save(buffer, format="JPEG")
        st.download_button(
            label="Download Headshot",
            data=buffer.getvalue(),
            file_name="headshot.jpg",
            mime="image/jpeg",
            help="Download the processed headshot as a JPEG file (annotation-free)."
        )

if __name__ == "__main__":
    main()
"""CAPTCHA system for Streamlit applications."""

import streamlit as st
import random
from typing import Tuple
from num2words import num2words
from operator import add, sub, mul

from .utils.logger import get_logger

logger = get_logger(__name__)


class StreamlitCaptcha:
    """A sophisticated CAPTCHA system for Streamlit apps with math problems and UI tricks."""
    
    def __init__(self, max_attempts: int = 2):
        """Initialize the CAPTCHA system.
        
        Args:
            max_attempts: Maximum number of skip attempts allowed
        """
        self.max_attempts = max_attempts
        self._initialize_session_state()
        logger.debug("CAPTCHA system initialized")
    
    def _initialize_session_state(self) -> None:
        """Initialize CAPTCHA-related session state variables."""
        if 'captcha_verified' not in st.session_state:
            st.session_state.captcha_verified = False
            st.session_state.captcha_attempts = 0
            st.session_state.button_assignment = random.choice(['submit', 'cancel'])
            self._generate_captcha()

    def _generate_captcha(self) -> None:
        """Generate a math CAPTCHA with one number as text."""
        num1 = random.randint(0, 10)  # Smaller range for simplicity
        num2 = random.randint(0, 10)
        operators = {'+': add, '-': sub, '*': mul}
        operator = random.choice(list(operators.keys()))
        
        # Ensure subtraction doesn't result in negative numbers
        if operator == '-' and num1 < num2:
            num1, num2 = num2, num1
        
        # Randomly convert one number to text
        num1_str = num2words(num1).title() if random.choice([True, False]) else str(num1)
        num2_str = str(num2) if num1_str != str(num1) else num2words(num2).title()
        
        st.session_state.captcha_question = f"What is {num1_str} {operator} {num2_str}?"
        st.session_state.captcha_answer = operators[operator](num1, num2)
        st.session_state.button_assignment = random.choice(['submit', 'cancel'])
        
        logger.debug(f"Generated CAPTCHA: {st.session_state.captcha_question} = {st.session_state.captcha_answer}")

    def _is_correct_button_clicked(self, button1_clicked: bool, button2_clicked: bool) -> bool:
        """Check if the correct button (Submit) was clicked based on randomized positions."""
        # Determine which button should be the Submit button
        submit_is_button1 = st.session_state.button_assignment == 'submit'
        
        # Return True if the correct Submit button was clicked
        return (button1_clicked and submit_is_button1) or (button2_clicked and not submit_is_button1)
    
    def _handle_captcha_submission(self, button1_clicked: bool, button2_clicked: bool, user_answer: str) -> None:
        """Handle CAPTCHA form submission with validation.
        
        Args:
            button1_clicked: Whether button1 was clicked
            button2_clicked: Whether button2 was clicked
            user_answer: User's input answer
        """
        # Check if correct button (Submit) was clicked
        if not self._is_correct_button_clicked(button1_clicked, button2_clicked):
            st.error("❌ **You clicked the wrong button.** Please try again.")
            self._handle_failed_attempt()
            return
            
        # Validate input format - allow negative numbers
        cleaned_input = user_answer.strip().replace('+', '')
        if not cleaned_input:
            st.error("❌ **Please enter an answer before clicking Submit.**")
            self._handle_failed_attempt()
            return
        elif not (cleaned_input.lstrip('-').isdigit()):
            st.error("❌ **Please enter a valid number (digits only, negative numbers allowed).**")
            self._handle_failed_attempt()
            return
            
        # Check if answer is correct
        try:
            if int(user_answer.strip()) == st.session_state.captcha_answer:
                st.session_state.captcha_verified = True
                st.success("✅ **Verification successful!** You can now use the app.")
                self._clear_captcha_data()
                logger.info("CAPTCHA verification successful")
                st.rerun()  # Refresh to show main app
            else:
                st.error("❌ **Incorrect answer.** Please try again.")
                self._handle_failed_attempt()
        except ValueError:
            st.error("❌ **Invalid input format.** Please enter a number.")
            self._handle_failed_attempt()


    def _handle_failed_attempt(self) -> None:
        """Handle failed CAPTCHA attempts and manage skips."""
        if st.session_state.captcha_attempts < self.max_attempts:
            st.session_state.captcha_attempts += 1
            self._generate_captcha()
            logger.info(f"CAPTCHA attempt failed, attempts: {st.session_state.captcha_attempts}/{self.max_attempts}")
            st.rerun()
        else:
            st.write("No more attempts available. Please solve this puzzle.")
            logger.warning("CAPTCHA max attempts reached")

    def _clear_captcha_data(self) -> None:
        """Clear CAPTCHA-related session state data."""
        captcha_keys = ['captcha_question', 'captcha_answer', 'captcha_attempts', 'button_assignment']
        for key in captcha_keys:
            if key in st.session_state:
                del st.session_state[key]
        logger.debug("CAPTCHA data cleared")

    def display_captcha(self) -> None:
        """Display CAPTCHA using standard Streamlit components in a clean, centered form."""
        # Center the CAPTCHA form on the page
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Create a bordered container for the CAPTCHA
            with st.container(border=True):
                # Title and description
                st.markdown("### 🔐 Security Verification")
                st.markdown("Please solve this math problem to continue:")
                
                # Display the math question prominently
                st.markdown(f"#### 🧮 **{st.session_state.captcha_question}**")
                
                # Skip button with remaining attempts info (outside the form if available)
                remaining_skips = self.max_attempts - st.session_state.captcha_attempts
                if remaining_skips > 0:
                    skip_button_label = f"🎲 Skip and Get New Problem ({remaining_skips} remaining)"
                    if st.button(skip_button_label, type="secondary", width="stretch"):
                        st.session_state.captcha_attempts += 1
                        self._generate_captcha()
                        logger.info(f"CAPTCHA skipped, attempts: {st.session_state.captcha_attempts}/{self.max_attempts}")
                        st.rerun()
                        return
                    st.divider()
                else:
                    st.warning("⚠️ **No more skips available.** Please solve this puzzle.")
                
                # Main CAPTCHA form
                with st.form(key="captcha_form", clear_on_submit=False):
                    # Input field
                    user_answer = st.text_input(
                        "Your Answer:",
                        key="captcha_input",
                        placeholder="Enter the result (numbers only)",
                        help="Type your answer and press Enter, or click the correct Submit button below",
                        label_visibility="visible"
                    )
                    
                    # Helpful hint
                    st.caption("💡 **Tip:** Both buttons are active - choose the correct 'Submit' button!")
                    
                    st.markdown("")
                    
                    # Dual submit buttons with randomized positions
                    # Note: Buttons are always enabled since Streamlit forms don't react to input changes
                    button_col1, button_col2 = st.columns(2)
                    button1_label = "✅ Submit" if st.session_state.button_assignment == 'submit' else "❌ Cancel"
                    button2_label = "❌ Cancel" if st.session_state.button_assignment == 'submit' else "✅ Submit"
                    
                    with button_col1:
                        button1_clicked = st.form_submit_button(
                            button1_label,
                            type="primary" if "Submit" in button1_label else "secondary",
                            width="stretch"
                        )
                    
                    with button_col2:
                        button2_clicked = st.form_submit_button(
                            button2_label,
                            type="primary" if "Submit" in button2_label else "secondary", 
                            width="stretch"
                        )
                    
                    # Handle form submission
                    if button1_clicked or button2_clicked:
                        self._handle_captcha_submission(button1_clicked, button2_clicked, user_answer)

    def is_verified(self) -> bool:
        """Check if the CAPTCHA has been verified.
        
        Returns:
            True if CAPTCHA is verified, False otherwise
        """
        return st.session_state.get('captcha_verified', False)
    
    def reset(self) -> None:
        """Reset the CAPTCHA system (useful for testing or re-verification)."""
        st.session_state.captcha_verified = False
        st.session_state.captcha_attempts = 0
        self._generate_captcha()
        logger.info("CAPTCHA system reset")

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

    def _create_buttons(self) -> Tuple[bool, bool]:
        """Create and return the state of dual buttons with random positions.
        
        Returns:
            Tuple of (button1_clicked, button2_clicked)
        """
        col1, col2 = st.columns(2)
        button1_label = "Submit" if st.session_state.button_assignment == 'submit' else "Cancel"
        button2_label = "Cancel" if st.session_state.button_assignment == 'submit' else "Submit"
        
        is_valid_input = st.session_state.get('captcha_input', '').strip() and \
                         st.session_state.get('captcha_input', '').replace('-', '').isdigit()
        
        with col1:
            button1_clicked = st.button(button1_label, key="button1", disabled=not is_valid_input)
        with col2:
            button2_clicked = st.button(button2_label, key="button2", disabled=not is_valid_input)
        
        return button1_clicked, button2_clicked

    def _is_correct_button_clicked(self, button1_clicked: bool, button2_clicked: bool) -> bool:
        """Check if the correct button was clicked.
        
        Args:
            button1_clicked: Whether button1 was clicked
            button2_clicked: Whether button2 was clicked
            
        Returns:
            True if the correct button was clicked
        """
        return (button1_clicked and st.session_state.button_assignment == 'submit') or \
               (button2_clicked and st.session_state.button_assignment == 'cancel')

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

    def display_captcha(self, title: str = "Please verify you're not a bot") -> None:
        """Display CAPTCHA and verify user input with dual buttons.
        
        Args:
            title: Title to display above the CAPTCHA
        """
        st.subheader(title)
        st.write(st.session_state.captcha_question)
        
        remaining_skips = self.max_attempts - st.session_state.captcha_attempts
        if remaining_skips > 0:
            st.write(f"💡 Skips remaining: {remaining_skips}")
            
            if st.button("🎲 Skip and Choose Another", key="skip_captcha"):
                st.session_state.captcha_attempts += 1
                self._generate_captcha()
                st.rerun()
        else:
            st.write("⚠️ No more skips available. Please solve this puzzle.")
        
        user_answer = st.text_input("Enter your answer:", key="captcha_input")
        button1_clicked, button2_clicked = self._create_buttons()
        
        if button1_clicked or button2_clicked:
            # Check if correct button was clicked
            if not self._is_correct_button_clicked(button1_clicked, button2_clicked):
                st.error("❌ You clicked the wrong button. Please try again.")
                self._handle_failed_attempt()
                return
                
            # Validate input
            if not user_answer.strip() or not user_answer.replace('-', '').isdigit():
                st.error("❌ Please enter a valid number.")
                self._handle_failed_attempt()
                return
                
            # Check answer
            if int(user_answer) == st.session_state.captcha_answer:
                st.session_state.captcha_verified = True
                st.success("✅ Verification successful! You can now use the app.")
                self._clear_captcha_data()
                logger.info("CAPTCHA verification successful")
                st.rerun()  # Refresh to show main app
            else:
                st.error("❌ Incorrect answer. Please try again.")
                self._handle_failed_attempt()

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

import os, time, PyPDF2, asyncio
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
import xml.etree.ElementTree as ET
from utils.logging import Logger

class GeminiService:
    """A class to encapsulate Gemini API functionality, PDF processing, and sitemap handling."""

    def __init__(self, api_key, logger=None):
        self.logger = logger or Logger.get_logger(
            name=__name__,
            log_level="DEBUG",
            log_file="logs/gemini.log"
        )
        self.api_key = api_key
        self._configure_genai()
        self.load_pdf_context("docs/portone_docs.pdf")
        self.load_sitemap_links("sitemap.xml")

    def _configure_genai(self):
        """Configure the Generative AI model and settings."""
        self.logger.info("Configuring Gemini API.")
        genai.configure(api_key=self.api_key)

        self.generation_config = GenerationConfig(
            temperature=1,
            max_output_tokens=8192,
        )

        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        self.model_flash = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=self.generation_config,
            safety_settings=self.safety_settings,
        )

    def load_pdf_context(self, pdf_path):
        """Load PDF content and cache it as a dictionary string."""
        self.logger.info(f"Loading PDF context from {pdf_path}.")
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)

                page_dict = {}
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    page_dict[page_num + 1] = page_text  # Page numbers start from 1

                self.pdf_context = str(page_dict)
                self.logger.info(f"Loaded {num_pages} pages from {pdf_path}.")
        except Exception as e:
            self.logger.error("Failed to load PDF content.", exc_info=e)
            raise

    def load_sitemap_links(self, sitemap_path):
        """Parse the sitemap XML and store links as a string."""
        self.logger.info(f"Loading sitemap links from {sitemap_path}.")
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            urls = [
                url.text
                for url in root.iterfind('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            ]
            self.sitemap_links = "\n".join([f"Link: {url}" for url in urls])
            self.logger.info(f"Loaded {len(urls)} links from {sitemap_path}.")
        except ET.ParseError as e:
            self.logger.error("Error parsing sitemap.xml.", exc_info=e)
            self.sitemap_links = ""
            raise

    async def generate_response(self, message):
        """Generate a response from the Gemini API based on the input message."""
        if not self.pdf_context or not self.sitemap_links:
            self.logger.error("PDF Contex is, %s", self.pdf_context)
            self.logger.error("Sitemap Links is, %s", self.sitemap_links)
            raise ValueError("PDF context or sitemap links are not loaded. Please initialize them.")

        self.logger.info(f"Generating response for message: {message}")

        # If message is a list (like user_history), join it into a single string
        if isinstance(message, list):
            message = "\n".join(message)

        # Combine the prompt parts into a single string
        prompt = "\n".join([
            '''
            Below are documents from XYZ, a financial services company offering payment aggregation services through API, dashboard, and mobile SDK solutions for businesses.
            Base link for the documentation: https://xyz.com. In this documentation, ✅ indicates the correct information, and ❌ indicates incorrect information.
            ''',
            self.pdf_context,
            f"Here are some relevant links from the sitemap:\n{self.sitemap_links}",
            '''
            You are a super helpful customer support representative bot on Discord and Slack for PortOne.
            Be friendly and fun to talk to, and provide helpful information to users who reach out to you.
            Also, provide code snippets or links to the documentation when necessary. Do not give invalid links or code snippets.
            Adhere strictly to the content provided in the documentation, and do not provide any information that is not present in the documentation.
            A user has reached out with the following query:
            ''',
            message,
        ])


        # Log execution time for debugging
        start_time = time.time()
        try:
            response = await asyncio.to_thread(self.model_flash.generate_content, prompt)
            end_time = time.time()
            self.logger.info(f"Gemini API call took {end_time - start_time:.2f} seconds.")
            return response.text
        except Exception as e:
            self.logger.error("Error generating response from Gemini API.", exc_info=e)
            raise

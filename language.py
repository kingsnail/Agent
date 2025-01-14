class Language():
 
    def __init__(self) -> None:
        self.language_code = "en"

    def get_language_code(self):
       return self.language_code
      
    def set_to_farsi(self) -> None:
        print("set_to_farsi() called.")
        self.language_code = "fa"
      
    def set_to_english(self) -> None:
        print("set_to_english() called.")
        self.language_code = "en"
      

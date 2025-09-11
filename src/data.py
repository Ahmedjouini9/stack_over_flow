import logging    
from core.data_extractor import DataExtractor


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataE(DataExtractor):
    def __init__(self, csv_filepath):
        self.csv_filepath = csv_filepath
        self.data = []


    
def main():
    extractor = DataExtractor()
    extractor.process_urls_from_csv(r"C:\Users\ahmed\Desktop\stack_over_flow\src\test.csv")
    # Now extractor.data contains all the scraped data
    # You can save it to a file or process it further
    extractor.save_to_json("scraped_data.json")


if __name__ == "__main__":
    main()

    

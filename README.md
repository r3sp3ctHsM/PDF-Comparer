# PDF Comparison Tool

This project is a PDF comparison tool that highlights differenes between PDF documents. It uses 'PyMuPDF' for PDF handling, 'Pillow' for image processing, 'numpy' for numerical operations.

## Features
• Compare two folders PDF documents and highlight differences (Names must match).

• Multithreading and Batch processing to handle large batches of PDF files efficiently.

• Image processing to overlay differences.

• Text comparison to identify word-level differences

## Requirements
• Python 3.6 or higher

## Dependencies

The project requires the following Python libraries

• PyMuPDF

• Pillow

• numpy

## Installation

Follow these steps to set up the project on your local machine.

### Step 1: Clone the Repository
```bash
git clone https://github.com/r3sp3ctHsM/Replit-Code.git
cd pdf-comparison-tool
```

### Step 2: Create a Virtual Environment (Optional but recommended)
```bash
python3 -m venv myenv
```

### Step 2.1: Activate the Virtual Environment
- On Windows:
```bash
myenv\Scripts\activate
```
- On macOS and Linux:
```bash
source myenv/bin/activate
```

### Step 3: Install the Dependencies
- On Windows:
```bash
pip install -r requirements.txt
```
- On macOS and Linux:
```bash
pip3 install -r requirements.txt
```

### Step 5: Verify the Installation (Optional but recommended

Ensure that the dependencies are installed correctly:
```bash
pip list
```

## Configuration

The project uses a configuration file ('config.json') to manage settings such as directories, quality, font size, batch size, and core count. You can customize these settings by editing the 'config.json' file.

### Example 'config.json'

```json
{
    "old_documents_dir": "./Old_Documents",
    "new_documents_dir": ".New_Documents",
    "output_dir": "./Output",
    "quality": 2.0,
    "font_size": 8.0,
    "batch_size": 4,
    "core_count": null # Set this to null to use the default calculation (1.5 times the number of CPU cores)
}
```

If 'core_count' is set to 'null', the script will automatically use 'os.cpu_count() * 1.5' to determine the number of cores.

# Usage

To run the PDF comparison tool, follow these steps:

1. Ensure you have the old and new PDF documents in the specified directories.
2. Update the 'config.json' file with the paths to your directories and desired settings.

### Example Usage
```bash
python main.py
```

## Output

The results will be saved in the directory specified in 'output_dir' in the 'config.json' file. Each document will have its own directory containing images of pages with differences highlighted.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

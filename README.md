# PDF Comparison Tool

This project is a PDF comparison tool that highlights differenes between PDF documents. It uses 'PyMuPDF' for PDF handling, 'Pillow' for image processing, 'numpy' for numerical operations. This tool saves the results as images grouped by document.

<ins> **Administrator rights are not required for this script.** </ins>

## Features
- Compare two folders PDF documents and highlight differences (Names must match).
- Multithreading and Batch processing to handle large batches of PDF files efficiently.
- Image processing to overlay differences.
- Text comparison to identify word-level differences

## Requirements
- Python 3.6 or higher
- pip3 (should be included with Python installs from Python 3.4 onwards)

## Dependencies

The project requires the following Python libraries
- PyMuPDF
- Pillow
- numpy

## Installation

Follow these steps to set up the project on your local machine.

### Step 1: Clone the Repository (this will create a folder name 'PDF-Comparer' in your current directory)
```bash
git clone https://github.com/r3sp3ctHsM/PDF-Comparer.git
cd PDF-Comparer
```

### Step 2: Create a Virtual Environment (only needs to be done once)
```bash
python3 -m venv myenv
```

### Step 3: Activate the Virtual Environment
- On Windows:
```bash
myenv\Scripts\activate
```
- On macOS and Linux:
```bash
source myenv/bin/activate
```

### Step 4: Install the Dependencies
```bash
pip3 install -r requirements.txt
```

### Step 5: Verify the Installation (Optional but recommended)

Ensure that the dependencies are installed correctly:
```bash
pip3 list
```

## Configuration

The project uses a configuration file ('config.json') to manage settings such as directories, quality, font size, batch size, and core count. You can customize these settings by editing the 'config.json' file.

1. Edit the 'config.json' file to specify your directories and settings:

```json
{
    "old_documents_dir": "./Old_Documents", # Set a to user-owned directory
    "new_documents_dir": ".New_Documents", # Set a to user-owned directory
    "output_dir": "./Output", # Set a to user-owned directory
    "quality": 2.0,
    "font_size": 8.0,
    "batch_size": 4,
    "core_count": null # Set this to null to use the default calculation (1.5 times the number of CPU cores)
}
```
If 'core_count' is set to 'null', the script will automatically use `os.cpu_count() * 1.5` to determine the number of cores.

### Examples of User-Owned Directories:

- **Windows**:
    - `C:\Users\YourUsername`
    - `C:\Users\YourUsername\Documents`
    - `C:\Users\YourUsername\Desktop`
    - `C:\Users\YourUsername\Downloads`

- **macOS**:
    - `/Users/YourUsername`
    - `/Users/YourUsername/Documents`
    - `/Users/YourUsername/Desktop`
    - `/Users/YourUsername/Downloads`

- **Linux**:
    - `/home/YourUsername`
    - `/home/YourUsername/Documents`
    - `/home/YourUsername/Desktop`
    - `/home/YourUsername/Downloads`

# Usage

To run the PDF comparison tool, follow these steps:

### 1. Ensure you have the old and new PDF documents in the specified directories.
- **Matching Document Names**: Ensure that the names of the new and old documents match exactly for the comparison tool to work correctly. For example, if you have ```document1.pdf``` in the ```Old_Documents``` directory, you should have ```document1.pdf``` in the ```New_Documents``` directory as well.

### 2. Update the 'config.json' file with the paths to your directories and desired settings.
- To avoid admin rights, please use [user-owned directories](#examples-of-user-owned-directories).

### 3. Ensure the terminal is in the 'pdf-comparison-tool' folder. If not, navigate to it (replace 'path/to' with install location):
```bash
cd path/to/PDF-Comparer
```
- If you followed the installation steps, this would be:
```bash
cd PDF-Comparer
```

#### Example Locations of Default Working Directories:

- On Windows (Command Promt or PowerShell):
    - Default: `C:\Users\YourUsername`
    - Navigate to project directory:
      ```bash
      cd C:\Users\YourUsername\PDF-Comparer
      ```

- On macOS and Linux (Terminal):
    - Default: `/Users/YourUsername` (macOS) or `/home/YourUsername` (Linux)
    - Navigate to project directory:
        - (macOS):
        ```bash
        cd /Users/YourUsername/PDF-Comparer
        ```
        - (Linux):
        ```bash
        cd /home/YourUsername/PDF-Comparer
        ```    

### 4. Activate the virtual environment if it's not already activated (needs to be done every time you open a new terminal session):
- On Windows:
   ```bash
   myenv\Scripts\activate
   ```
- On macOS and Linux:
   ```bash
   source myenv/bin/activate
   ```

### 5. Run the PDF comparison tool:
```bash
python pdfcomparer.py
```

## Output

The results will be saved in the directory specified in 'output_dir' in the 'config.json' file. Each document will have its own directory containing images of pages with differences highlighted.

## Additional Notes

- **Updating Dependencies**: To update deendencies, you can run `pip3 install --upgrade -r requirements.txt`.
- **Memory Usage**: Be mindful of memory usage when processing large PDF files. Consider increasing the system's available memory or processing smaller batches.
- **Font Loading**: If you encounter issues with font loading, add the `Arial.ttf` font file into the project directory

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Create a new Pull Request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

# GitCloner
GitCloner is a Python tool designed to clone files from the '.git' directory of web applications where directory listing is disabled. It allows you to retrieve specific files from the Git repository using various options and configurations.

## Usage
To use GitCloner, simply run the `git_cloner.py` script with the following command:

```bash
usage: git_cloner.py [-h] [--working_directory WORKING_DIRECTORY] [--data_directory DATA_DIRECTORY]
                     [--white_list_extensions [WHITE_LIST_EXTENSIONS ...]] [--interactive_cli] [--read_only]
                     [--disable_highlighting] [--style_mode {0,1}] [--depth DEPTH]
                     target_url
```

### Positional Argument:
- \`target_url\`: URL of the target web application (e.g., http(s)://www\.example\.com/).

### Options:
- \`-h, --help\`: Show the help message and exit.
- \`--working_directory WORKING_DIRECTORY\`: Specify the name of the working directory where the '.git' files will be downloaded. Default is 'working_directory'.
- \`--data_directory DATA_DIRECTORY\`: Specify the name of the data directory where the actual files will be downloaded. Default is 'data_directory'.
- \`--white_list_extensions [WHITE_LIST_EXTENSIONS ...]\`: List of allowed file extensions to download (e.g., html js php).
- \`--interactive_cli\`: Enable interactive command line interface (default: False).
- \`--read_only\`: Enable read-only mode (default: False). Only available when \`--interactive_cli\` is enabled.
- \`--disable_highlighting\`: Disable highlighting mode (default: False). Only available when \`--read_only\` is enabled.
- \`--style_mode {0,1}\`: Set the style mode 0 or 1 (default: 0). Only available when \`--interactive_cli\` is enabled.
- \`--depth DEPTH\`: Depth of commits to clone (default is all).

## Video Demonstration
You can watch a video demonstration of how to use GitCloner ![Watch the video](https://github.com/ma4747gh/GitCloner/raw/main/GitCloner.ogv).

## Author
Coded by Mohamed Ahmed (ma4747gh).

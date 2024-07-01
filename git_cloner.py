from rich.console import Console
from rich import print_json
from rich.panel import Panel
from rich import box
import argparse
import requests
import os
import shlex
import subprocess
import re
import json


class GitCloner:
    def __init__(self):
        self.console = Console()
        self.args = self.initialize_argparse()

        self.target_url = self.args.target_url if self.args.target_url.endswith('/') else self.args.target_url + '/'
        self.current_reference = None
        self.current_commit_hash = None

        self.hierarchy = {}
        self.current_depth = 0

        self.blob_names = {}

        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.current_dir = None

    def initialize_argparse(self):
        parser = argparse.ArgumentParser(description='GitCloner is a tool used to clone all possible files from the '
                                                     '\'.git\' directory in a web application where directory listing '
                                                     'is disabled. The tool is interactive and highly flexible for '
                                                     'downloading specific files.',
                                         epilog='Coded by Mohamed Ahmed (ma4747gh).')

        parser.add_argument('target_url',
                            help='Please input the URL of the target web application (e.g., '
                                 'http(s)://www.example.com/).')
        parser.add_argument('--working_directory',
                            help='Specify the name of the working directory where the \'.git\' files will be '
                                 'downloaded. If no name is chosen, the default name is \'working_directory\' (note: '
                                 'this is not the actual files).',
                            default='working_directory')
        parser.add_argument('--data_directory',
                            help='Specify the name of the data directory where the actual files will be downloaded. '
                                 'If no name is chosen, the default name is \'data_directory\'.',
                            default='data_directory')
        parser.add_argument('--white_list_extensions',
                            help='List of allowed file extensions (e.g., html js php).',
                            nargs='*')
        parser.add_argument('--interactive_cli',
                            help='Enable interactive command line interface (default: False).',
                            action='store_true')
        parser.add_argument('--read_only',
                            help='Enable read-only mode (default: False). Only available when --interactive_cli is '
                                 'enabled.',
                            action='store_true')
        parser.add_argument('--disable_highlighting',
                            help='Disable highlighting mode (default: False). Only available when --read_only is '
                                 'enabled.',
                            action='store_true')
        parser.add_argument('--style_mode',
                            help='Set the style mode 0 or 1 (default: 0). Only available when --interactive_cli is '
                                 'enabled',
                            default=0,
                            type=int,
                            choices=[0, 1])
        parser.add_argument('--depth',
                            help='Depth of commits to clone (default is all).',
                            default=None,
                            type=int)

        args = parser.parse_args()

        if args.read_only and (not args.interactive_cli):
            self.console.print('\n[bold red][-] --read_only can only be used with --interactive_cli enabled.[/bold red]')
            exit()

        if args.style_mode and (not args.read_only):
            self.console.print('\n[bold red][-] --style_mode can only be used with --read_only enabled.[/bold red]')
            exit()

        if args.disable_highlighting and (not args.read_only):
            self.console.print('\n[bold red][-] --disable_highlighting can only be used with --read_only enabled.[/bold red]')
            exit()

        return parser.parse_args()

    def check_if_git_endpoint_found(self):
        response = requests.get(self.target_url + '.git')

        if response.status_code == 200:
            self.console.print('\n[bold green][+] \'.git\' endpoint found.[/bold green]')
        else:
            self.console.print('\n[bold red][-] \'.git\' endpoint not found.[/bold red]')
            exit()

    def create_new_working_directory(self):
        new_directory = self.args.working_directory
        os.makedirs(new_directory, exist_ok=True)
        os.chdir(new_directory)

        if not os.path.isdir('.git'):
            command = 'git init'
            args = shlex.split(command)
            subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.console.print('\n[bold green][+] git folder initialized.[/bold green]')

        os.chdir('.git')

    def extract_current_reference_from_head_file(self):
        response = requests.get(self.target_url + '.git/HEAD')

        self.current_reference = response.text.strip().split(': ')[1]
        self.console.print('\n[bold green][+] \'{}\' reference found.[/bold green]'.format(self.current_reference))

    def extract_current_commit_hash_from_current_reference(self):
        response = requests.get(self.target_url + '.git/' + self.current_reference)

        self.current_commit_hash = response.text.strip()

    def download_object(self, object_hash):
        object_folder, object_file = object_hash[:2], object_hash[2:]
        os.makedirs('objects/{}'.format(object_folder), exist_ok=True)

        response = requests.get(self.target_url + '.git/objects/{}/{}'.format(object_folder, object_file))

        with open('objects/{}/{}'.format(object_folder, object_file), 'wb') as file:
            file.write(response.content)

        command = 'git cat-file -t {}'.format(object_hash)
        args = shlex.split(command)
        object_type = subprocess.run(args, capture_output=True).stdout.strip().decode()

        if object_type == 'commit':
            self.hierarchy[self.current_depth] = {
                'commit_hash': object_hash,
                'tree': {}
            }

            command = 'git cat-file -p {}'.format(object_hash)
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True).stdout.decode()

            tree_hashes = re.findall(r'tree (.*)\n', result)
            tree_hash = tree_hashes[0] if tree_hashes else None

            self.hierarchy[self.current_depth]['tree'] = self.download_object(tree_hash)

            parent_hashes = re.findall(r'parent (.*)\n', result)
            parent_hash = parent_hashes[0] if parent_hashes else None

            return parent_hash

        elif object_type == 'tree':
            current_tree = {
                'tree_hash': object_hash,
                'name': None,
                'subtrees': [],
                'blobs': []
            }

            command = 'git cat-file -p {}'.format(object_hash)
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True).stdout.decode()

            blobs = re.findall(r'blob (.*)\t(.*)\n', result)
            for blob_hash, blob_name in blobs:
                if self.args.white_list_extensions and blob_name.split('.')[-1] not in self.args.white_list_extensions:
                    continue

                current_tree['blobs'].append({
                    'blob_hash': blob_hash,
                    'blob_name': blob_name
                })

                if self.args.interactive_cli:
                    if blob_hash not in self.blob_names:
                        self.blob_names[blob_hash] = blob_name

            trees = re.findall(r'tree (.*)\t(.*)\n', result)
            for tree_hash, tree_name in trees:
                subtree = self.download_object(tree_hash)
                subtree['tree_hash'] = tree_hash
                subtree['name'] = tree_name
                current_tree['subtrees'].append(subtree)

            return current_tree

        else:
            command = 'git cat-file -p {}'.format(object_hash)
            args = shlex.split(command)
            result = subprocess.run(args, capture_output=True).stdout

            return result

    def construct_hierarchy(self):
        while True:
            parent_hash = self.download_object(self.current_commit_hash)
            if parent_hash:
                self.current_commit_hash = parent_hash
                self.current_depth += 1
                if self.current_depth == self.args.depth:
                    break
            else:
                break

    def create_data_directory(self):
        new_directory = self.args.data_directory
        self.current_dir = self.dir + '/' + new_directory
        os.makedirs(self.current_dir, exist_ok=True)

    def clone_hierarchy(self):
        for key, value in self.hierarchy.items():
            new_directory = 'commit_{}'.format(key)
            self.current_dir = self.current_dir + '/' + new_directory
            os.makedirs(self.current_dir, exist_ok=True)

            self.clone_tree(value['tree'])
        self.console.print('\n[bold green][+] Cloning finished.[/bold green]')

    def clone_tree(self, tree):
        if tree['name']:
            new_directory = tree['name']
            self.current_dir = self.current_dir + '/' + new_directory
            os.makedirs(self.current_dir, exist_ok=True)

        for blob in tree['blobs']:
            data = self.download_object(blob['blob_hash'])
            with open(self.current_dir + '/' + blob['blob_name'], 'wb') as file:
                file.write(data)

        for subtree in tree['subtrees']:
            self.clone_tree(subtree)

        self.current_dir = '/'.join(self.current_dir.split('/')[:-1])

    def interactive_cli(self):
        if self.args.disable_highlighting:
            json_str = json.dumps(self.hierarchy, indent=4)
            self.console.print('\n', end='')
            print_json(json_str)
        else:
            highlighted_data = self.highlight_extension_files(self.hierarchy)
            json_str = json.dumps(highlighted_data, indent=4)
            self.console.print('\n', end='')
            self.console.print(json_str)

        if not self.args.read_only:
            self.console.print('\n[bold green]Enter a list of hashes for the intended files from the previous JSON '
                               'file, separated by spaces: [/bold green]',
                               end='')
            user_choices_list = input().split()
            for user_choice in user_choices_list:
                self.clone_file(user_choice)
            self.console.print('\n[bold green][+] Cloning finished.[/bold green]')
        else:
            while True:
                self.console.print('\n[bold green]Please enter the hash of the file you intend to read from the '
                                   'previous JSON file (note: only one file at a time). Enter \'exit\' if you want to '
                                   'exit: [/bold green]',
                                   end='')
                user_choice = input()
                if user_choice == 'exit':
                    exit()
                else:
                    self.read_file(user_choice)

    def highlight_extension_files(self, data):
        if isinstance(data, dict):
            return {k: self.highlight_extension_files(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.highlight_extension_files(v) for v in data]
        elif isinstance(data, str) and re.search(r'\.\w+$', data):
            return '[#FFF5E1 on #C80036]{}[/#FFF5E1 on #C80036]'.format(data)
        else:
            return data

    def clone_file(self, file_hash):
        data = self.download_object(file_hash)
        with open(self.current_dir + '/' + file_hash + '_' + self.blob_names[file_hash], 'wb') as file:
            file.write(data)

    def read_file(self, file_hash):
        data = self.download_object(file_hash)

        if self.args.style_mode == 0:
            panel = Panel(data.decode(), style='#EEEEEE on #373A40', box=box.MINIMAL)
            self.console.print('\n', end='')
            self.console.print(panel)
        else:
            self.console.print('\n', end='')
            self.console.print('[#EEEEEE on #373A40]' + data.decode() + '[/#EEEEEE on #373A40]')

    def start(self):
        self.check_if_git_endpoint_found()
        self.create_new_working_directory()
        self.extract_current_reference_from_head_file()
        self.extract_current_commit_hash_from_current_reference()
        self.construct_hierarchy()
        self.create_data_directory()

        if not self.args.interactive_cli:
            self.clone_hierarchy()
        else:
            self.interactive_cli()


git_cloner = GitCloner()
git_cloner.start()

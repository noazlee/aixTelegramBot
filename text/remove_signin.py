import os
import re

def clean_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Remove the sign-up and sign-in sections
    patterns = [
        r'Sign Up – Gamers Hideout.*?Signup for exclusive promotions, coupons and events\.',
        r'Register.*?Go to Sign In',
        r'Shopping Cart.*?Checkout'
    ]

    for pattern in patterns:
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # Remove extra whitespace and newlines
    content = re.sub(r'\n\s*\n', '\n\n', content)
    content = content.strip()

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def main():
    for filename in os.listdir('.'):
        if filename.endswith('.txt'):
            print(f"Cleaning {filename}...")
            clean_file(filename)
            print(f"Finished cleaning {filename}")

if __name__ == "__main__":
    main()
from .cli import Cli

def main():
    cli = Cli()
    cli.entryPoint()
    print('finish')

if __name__ == '__main__':
    main()
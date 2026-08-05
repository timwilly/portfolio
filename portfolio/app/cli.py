import click
import os

def register(app):
    @app.cli.command('import-businesses-once')
    @click.argument('csv_path', type=click.Path(
        exists=True, dir_okay=False, readable=True
    ))
    @click.option('--dry-run', is_flag=True,
                  help='Analyse les changements sans modifier la base de données.')
    def import_businesses_once_command(csv_path, dry_run):
        """Importe une seule fois les établissements depuis un fichier CSV."""
        from app.tasks import import_businesses_once

        result = import_businesses_once(csv_path, dry_run=dry_run)
        _print_business_import_result(result, dry_run)


    @app.cli.command('refresh-businesses-once')
    @click.option('--dry-run', is_flag=True,
                  help='Analyse les changements sans modifier la base de données.')
    def refresh_businesses_once_command(dry_run):
        """Télécharge puis importe les établissements de Montréal."""
        from app.tasks import refresh_businesses_once

        result = refresh_businesses_once(dry_run=dry_run)
        _print_business_import_result(result, dry_run, downloaded=True)


    def _print_business_import_result(result, dry_run, downloaded=False):
        action = 'Simulation terminée' if dry_run else 'Importation terminée'
        if downloaded:
            action = '{} après téléchargement'.format(action)
        click.echo(
            '{} en {:.2f} s: {} ajout(s), {} modification(s), '
            '{} suppression(s).'.format(
                action,
                result['duration_seconds'],
                result['created'],
                result['updated'],
                result['deleted']
            )
        )


    # Groupe d'application 'translate' et que l'on va ensuite ajouter des 
    # applications/commandes tel que 'init', 'update', etc.
    @app.cli.group()
    def translate():
        """Translation and localization commands."""
        pass


    # (venv) $ flask translate init <LANG>
    @translate.command()
    @click.argument('lang')
    def init(lang):
        """Initialize a new language."""
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel init -i messages.pot -d app/translations -l ' 
                    + lang):
            raise RuntimeError('init command failed')
        os.remove('messages.pot')


    # (venv) $ flask translate update
    @translate.command()
    def update():
        """Update all languages."""
        # Si retourne 0, commande exécuté sans erreur
        if os.system('pybabel extract -F babel.cfg -k _l -o messages.pot .'):
            raise RuntimeError('extract command failed')
        if os.system('pybabel update -i messages.pot -d app/translations'):
            raise RuntimeError('update command failed')
        os.remove('messages.pot')


    # (venv) $ flask translate compile
    @translate.command()
    def compile():
        """Compile all languages."""
        if os.system('pybabel compile -d app/translations'):
            raise RuntimeError('compile command failed')

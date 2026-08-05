from flask import current_app

"""
    Si elasticsearch n'existe pas on fait rien du tout.
    Comme ça l'application roulera comme habituel et si l'on décide
    de changer de 'search engine' on peut modifier ce fichier sans problème

"""
# 
def add_to_index(index, model):
    """
    Ajout d'un model dans elasticsearch
    Modifie un model déja indexé (en utilisant le même id)

    Args:
        index: Le nom du modèle a indexer dans elasticSearch
        model: L'instance du modèle

    """
    #print('add to index: {} {}'.format(index, model))
    #print(type(index))
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        #print('field : {}'.format(field))
        payload[field] = getattr(model, field)  # Trouver le field du modèle
    #print(model.id)
    #print(payload)
    
    try:
        current_app.elasticsearch.index(index=index, id=model.id, body=payload)
    except Exception as e:
        # Journaliser l'erreur si nécessaire
        print(f"Erreur lors de l'ajout à l'index dans Elasticsearch: {e}")

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    try:
        current_app.elasticsearch.delete(index=index, id=model.id)
    except Exception as e:
        # Journaliser l'erreur si nécessaire
        print(f"Erreur lors de la suppression de l'index dans Elasticsearch: {e}")


def query_index(index, query, page, per_page):
    #print('query index: {}, {}, {}, {}'.format(index, query, page, per_page))
    if not current_app.elasticsearch:
        return [], 0
    try:
        search = current_app.elasticsearch.search(
            index=index,
            body={
                'query': {'multi_match': {'query': query, 'fields': ['*']}},
                'from': (page - 1) * per_page, 'size': per_page
            }
        )        
    except Exception as e:
        # Journaliser l'erreur si nécessaire
        print(f"Erreur lors de la recherche dans Elasticsearch: {e}")
        return [], 0

    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    return ids, search['hits']['total']['value']
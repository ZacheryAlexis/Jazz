from app.src.embeddings.db_client import DataBaseClient
from app.src.core.ui import default_ui
from app.utils.ui_messages import UI_MESSAGES
import os


def handle_embed_request(*args):
    """Handle the /embed command to embed documents from a specified directory."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 2:
        default_ui.error(UI_MESSAGES["usage"]["embed"])
        return

    directory_path = args[0]
    collection_name = args[1]
    
    if len(collection_name) < 3:
        default_ui.error(UI_MESSAGES["errors"]["collection_name_too_short"])
        return

    if directory_path == "." or directory_path == "./":
        directory_path = os.getcwd()

    # Note: Not using 'with status()' context because it suppresses debug output and blocks stderr
    # The store_documents method includes its own status messages
    db_client.store_documents(directory_path, collection_name)


def handle_index_request(*args):
    """Handle the /index command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["index"])
        return

    collection_name = args[0]

    db_client.index_collection(collection_name)
    default_ui.status_message(
        title=UI_MESSAGES["titles"]["info"],
        message=UI_MESSAGES["success"]["collection_indexed"].format(collection_name),
        style="success",
    )


def handle_unindex_request(*args):
    """Handle the /unindex command to toggle indexing for a specified collection."""
    db_client = DataBaseClient.get_instance()

    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return

    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["unindex"])
        return

    collection_name = args[0]

    db_client.unindex_collection(collection_name)
    default_ui.status_message(
        title=UI_MESSAGES["titles"]["info"],
        message=UI_MESSAGES["success"]["collection_unindexed"].format(collection_name),
        style="success",
    )


def handle_list_command(*args):
    """
    Handle the /list command which lists collections in the database and
    whether they are indexed or not.
    """
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.list_collections()


def handle_delete_command(*args):
    """Handles the deletion of a collection from the database by its name."""
    db_client = DataBaseClient.get_instance()
    
    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"]["delete"])
        return
    
    collection_name = args[0]
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.delete_collection(collection_name=collection_name)
    

def handle_purge_command():
    """Handles the purging of all collections from the database."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.reset_database()


def handle_query_command(*args):
    """Handle the /query command to search embeddings."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    if len(args) < 1:
        default_ui.error(UI_MESSAGES["usage"].get("query", "Usage: /query <search_text>"))
        return
    
    query = " ".join(args)
    
    try:
        results = db_client.get_query_results(query, n_results=5)
        
        if not results:
            default_ui.status_message(
                title="Search Results",
                message="No matching documents found.",
                style="warning",
            )
            return
        
        # Format and display results
        output = []
        for i, (doc, meta) in enumerate(results, 1):
            file_path = meta.get("file_path", "Unknown")
            preview = doc[:150] + "..." if len(doc) > 150 else doc
            output.append(f"\n**Result {i}:** {file_path}\n{preview}")
        
        message = "\n".join(output)
        default_ui.status_message(
            title="Search Results",
            message=message,
            style="success",
        )
    except Exception as e:
        default_ui.error(f"Query failed: {e}")


def handle_collections_command(*args):
    """Handle the /collections command to list collections."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    db_client.list_collections()


def handle_list_all_docs_command(*args):
    """Handle the /list_all_docs command to list all unique documents in the knowledge base."""
    db_client = DataBaseClient.get_instance()
    
    if db_client is None:
        default_ui.error(
            UI_MESSAGES["errors"]["db_not_initialized"]
        )
        return
    
    try:
        import chromadb
        from pathlib import Path
        
        # Get all documents with metadata
        results = db_client.db_client.get_collection('archive').get(
            limit=50000,
            include=['metadatas']
        )
        
        # Extract unique file paths
        unique_files = set()
        for meta in results['metadatas']:
            if meta and 'file_path' in meta:
                unique_files.add(meta['file_path'])
        
        # Format output
        output = []
        for i, file_path in enumerate(sorted(unique_files), 1):
            output.append(f"{i}. {Path(file_path).name}")
        
        message = f"Total unique documents: {len(unique_files)}\n\n" + "\n".join(output)
        default_ui.status_message(
            title="All Documents in Knowledge Base",
            message=message,
            style="success",
        )
    except Exception as e:
        default_ui.error(f"Failed to list documents: {e}")

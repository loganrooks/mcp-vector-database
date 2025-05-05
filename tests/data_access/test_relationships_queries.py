import pytest
import psycopg
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

# Import functions from the new queries module
from src.philograph.data_access.queries import relationships as rel_queries
# Import models if needed for type hints or assertions
from src.philograph.data_access.models import Relationship
# Import utility functions if used directly in tests (though mocks are preferred)
from src.philograph.utils import db_utils

# --- Mock Fixtures (Example - Define or import actual fixtures) ---
@pytest.fixture
def mock_get_conn(mocker):
    """Fixture to mock the get_db_connection context manager."""
    mock_conn = AsyncMock(spec=psycopg.AsyncConnection)
    mock_cursor = AsyncMock(spec=psycopg.AsyncCursor)
    mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
    mock_cm = mocker.patch('src.philograph.data_access.connection.get_db_connection')
    mock_cm.return_value.__aenter__.return_value = mock_conn
    return mock_conn, mock_cursor

@pytest.fixture
def mock_json_serialize(mocker):
    """Fixture to mock the json_serialize utility."""
    return mocker.patch('src.philograph.data_access.queries.relationships.json_serialize')

# --- Test Reference Operations (Moved from original db_layer tests) ---

@pytest.mark.asyncio
async def test_add_reference_success(mock_json_serialize, mock_get_conn):
    """Tests successfully adding a reference."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (201,) # fetchone returns tuple

    source_chunk_id = 101 # Assuming a valid chunk ID
    cited_doc_details = {"title": "Cited Doc", "author": "Cited Author"}
    serialized_details = '{"title":"Cited Doc","author":"Cited Author"}' # Compact
    mock_json_serialize.return_value = serialized_details # Mock serialization

    expected_id = 201
    # Adjusted SQL based on implementation in relationships.py
    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (source_node_id, target_node_id, relation_type) DO NOTHING -- Avoid duplicates
        RETURNING id;
    """
    # Construct expected node IDs based on implementation
    expected_source_node = f"chunk:{source_chunk_id}"
    expected_target_node = f"citation:{cited_doc_details.get('doi', cited_doc_details.get('title', 'unknown'))}"
    expected_relation_type = "cites"
    expected_params = (expected_source_node, expected_target_node, expected_relation_type, serialized_details)

    # Call the function under test (using the new module path)
    returned_id = await rel_queries.add_reference(mock_conn, source_chunk_id, cited_doc_details)

    # Assertions
    mock_json_serialize.assert_called_once_with(cited_doc_details)
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    # mock_conn.commit.assert_awaited_once() # Commit handled by context manager
    assert returned_id == expected_id

@pytest.mark.asyncio
async def test_add_reference_invalid_chunk_id(mock_json_serialize, mock_get_conn):
    """Tests adding a reference with an invalid chunk_id raises IntegrityError."""
    # Note: This test assumes the DB raises IntegrityError for FK violation.
    # The add_reference implementation might catch this or let it propagate.
    # Adjusting test based on add_reference implementation which uses add_relationship.
    mock_conn, mock_cursor = mock_get_conn

    source_chunk_id = 999 # Non-existent chunk_id
    cited_doc_details = {"title": "Cited Doc"}
    serialized_details = '{"title":"Cited Doc"}'
    mock_json_serialize.return_value = serialized_details

    # Simulate psycopg.IntegrityError on execute within add_relationship
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK constraint violation")

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await rel_queries.add_reference(mock_conn, source_chunk_id, cited_doc_details)

    # Assertions
    mock_json_serialize.assert_called_once_with(cited_doc_details)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    # mock_conn.commit.assert_not_called() # Commit not called on error

# --- Test Relationship Operations ---

@pytest.mark.asyncio
async def test_add_relationship_success(mock_json_serialize, mock_get_conn):
    """Tests successfully adding a relationship."""
    mock_conn, mock_cursor = mock_get_conn

    # Simulate the RETURNING id from the database
    mock_cursor.fetchone.return_value = (301,) # fetchone returns tuple

    source_node_id = "doc:123"
    target_node_id = "chunk:456"
    relation_type = "cites"
    metadata = {"page": 42}
    serialized_metadata = '{"page":42}' # Compact
    mock_json_serialize.return_value = serialized_metadata

    expected_id = 301
    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    expected_params = (source_node_id, target_node_id, relation_type, serialized_metadata)

    # Call the function under test
    returned_id = await rel_queries.add_relationship(mock_conn, source_node_id, target_node_id, relation_type, metadata)

    # Assertions
    mock_json_serialize.assert_called_once_with(metadata)
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchone.assert_awaited_once()
    # mock_conn.commit.assert_awaited_once() # Commit handled by context manager
    assert returned_id == expected_id

@pytest.mark.asyncio
async def test_add_relationship_db_error(mock_json_serialize, mock_get_conn):
    """Tests that add_relationship propagates database errors."""
    mock_conn, mock_cursor = mock_get_conn

    source_node_id = "doc:123"
    target_node_id = "doc:999" # Assume invalid target
    relation_type = "related_to"
    metadata = None
    serialized_metadata = None
    mock_json_serialize.return_value = serialized_metadata

    # Simulate psycopg.IntegrityError on execute
    db_error = psycopg.IntegrityError("FK constraint violation")
    mock_cursor.execute.side_effect = db_error

    # Expect psycopg.IntegrityError to be raised and propagated
    with pytest.raises(psycopg.IntegrityError):
        await rel_queries.add_relationship(mock_conn, source_node_id, target_node_id, relation_type, metadata)

    # Assertions
    mock_json_serialize.assert_called_once_with(metadata)
    mock_cursor.execute.assert_awaited_once() # Ensure execute was called
    # mock_conn.commit.assert_not_called() # Commit not called on error

@pytest.mark.asyncio
async def test_get_relationships_outgoing_success(mock_get_conn):
    """Tests retrieving outgoing relationships successfully."""
    mock_conn, mock_cursor = mock_get_conn

    node_id = "doc:123"
    # Simulate DB result as tuples
    db_results_tuples = [
        (301, node_id, 'chunk:456', 'cites', {'page': 42}),
        (302, node_id, 'doc:789', 'related_to', None)
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s) ORDER BY created_at DESC;"
    expected_params = (node_id,)

    # Call the function under test
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='outgoing')

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2
    assert all(isinstance(rel, Relationship) for rel in relationships)
    assert relationships[0].id == db_results_tuples[0][0]
    assert relationships[0].target_node_id == db_results_tuples[0][2]
    assert relationships[0].metadata == db_results_tuples[0][4]
    assert relationships[1].metadata is None # Check None metadata remains None

@pytest.mark.asyncio
async def test_get_relationships_incoming_success(mock_get_conn):
    """Tests retrieving incoming relationships successfully."""
    mock_conn, mock_cursor = mock_get_conn

    node_id = "chunk:456"
    db_results_tuples = [
        (301, 'doc:123', node_id, 'cites', {'page': 42})
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (target_node_id = %s) ORDER BY created_at DESC;"
    expected_params = (node_id,)

    # Call the function under test
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='incoming')

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 1
    assert relationships[0].id == db_results_tuples[0][0]
    assert relationships[0].source_node_id == db_results_tuples[0][1]

@pytest.mark.asyncio
async def test_get_relationships_both_success(mock_get_conn):
    """Tests retrieving both incoming and outgoing relationships."""
    mock_conn, mock_cursor = mock_get_conn

    node_id = "doc:123"
    db_results_tuples = [
        (301, node_id, 'chunk:456', 'cites', None), # Outgoing
        (305, 'doc:999', node_id, 'cites', None)  # Incoming
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s OR target_node_id = %s) ORDER BY created_at DESC;"
    expected_params = (node_id, node_id)

    # Call the function under test
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='both')

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 2

@pytest.mark.asyncio
async def test_get_relationships_outgoing_with_type_filter(mock_get_conn):
    """Tests retrieving outgoing relationships filtered by type."""
    mock_conn, mock_cursor = mock_get_conn

    node_id = "doc:123"
    relation_type_filter = "cites"
    db_results_tuples = [
        (301, node_id, 'chunk:456', relation_type_filter, None)
    ] # Only the 'cites' relationship should be returned
    mock_cursor.fetchall.return_value = db_results_tuples

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s) AND relation_type = %s ORDER BY created_at DESC;"
    expected_params = (node_id, relation_type_filter)

    # Call the function under test
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='outgoing', relation_type=relation_type_filter)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships) == 1
    assert relationships[0].relation_type == relation_type_filter

@pytest.mark.asyncio
async def test_get_relationships_non_existent_node(mock_get_conn):
    """Tests retrieving relationships for a non-existent node returns an empty list."""
    mock_conn, mock_cursor = mock_get_conn

    node_id = "non:existent"
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = []

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s) ORDER BY created_at DESC;"
    expected_params = (node_id,)

    # Call the function under test (default direction is outgoing)
    relationships = await rel_queries.get_relationships(mock_conn, node_id)

    # Assertions
    # Match exact SQL string from source
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []

@pytest.mark.asyncio
async def test_get_relationships_for_document_success(mock_get_conn):
    """Tests retrieving relationships originating from chunks within a document."""
    mock_conn, mock_cursor = mock_get_conn

    doc_id = 123
    db_results_tuples = [
        (301, 'chunk:456', 'doc:789', 'cites', {'page': 10}),
        (302, 'chunk:457', 'doc:790', 'cites', None)
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    expected_sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s
        ORDER BY r.created_at DESC;
    """
    expected_params = (doc_id,)

    # Call the function under test
    relationships_dicts = await rel_queries.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    # Match exact SQL string from source (including whitespace)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert len(relationships_dicts) == 2
    # Check dict structure
    assert relationships_dicts[0]['id'] == db_results_tuples[0][0]
    assert relationships_dicts[0]['source_node_id'] == db_results_tuples[0][1]
    assert relationships_dicts[0]['metadata'] == db_results_tuples[0][4]
    assert relationships_dicts[1]['metadata'] is None # Check None metadata

@pytest.mark.asyncio
async def test_get_relationships_for_document_empty(mock_get_conn):
    """Tests retrieving relationships for a document with no relationships."""
    mock_conn, mock_cursor = mock_get_conn

    doc_id = 124
    # Simulate fetchall returning an empty list
    mock_cursor.fetchall.return_value = []

    expected_sql = """
        SELECT r.id, r.source_node_id, r.target_node_id, r.relation_type, r.metadata
        FROM relationships r
        JOIN chunks c ON r.source_node_id = 'chunk:' || c.id::text
        JOIN sections s ON c.section_id = s.id
        WHERE s.doc_id = %s
        ORDER BY r.created_at DESC;
    """
    expected_params = (doc_id,)

    # Call the function under test
    relationships = await rel_queries.get_relationships_for_document(mock_conn, doc_id)

    # Assertions
    # Match exact SQL string from source (including whitespace)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, expected_params)
    mock_cursor.fetchall.assert_awaited_once()
    assert relationships == []

# --- Additional Relationship Tests (from lines 1580+) ---

@pytest.mark.asyncio
async def test_add_relationship_cites_success_again(mock_json_serialize, mock_get_conn): # Renamed slightly
    """Tests adding a 'cites' relationship successfully."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.fetchone.return_value = (1,) # Simulate returning ID tuple

    source = "doc:1"
    target = "doc:2"
    rel_type = "cites"
    metadata = {"page": 5}
    serialized_metadata = '{"page":5}' # Compact
    mock_json_serialize.return_value = serialized_metadata

    result_id = await rel_queries.add_relationship(mock_conn, source, target, rel_type, metadata)

    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    # Match exact SQL string from source (including whitespace)
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (source, target, rel_type, serialized_metadata))
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert result_id == 1

@pytest.mark.asyncio
async def test_add_relationship_invalid_source_node_again(mock_json_serialize, mock_get_conn): # Renamed slightly
    """Tests adding relationship with invalid source node raises IntegrityError."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK violation")
    mock_json_serialize.return_value = None

    with pytest.raises(psycopg.IntegrityError):
        await rel_queries.add_relationship(mock_conn, "invalid:1", "doc:2", "cites")

    # mock_conn.commit.assert_not_called() # Handled by context manager

@pytest.mark.asyncio
async def test_add_relationship_invalid_target_node_again(mock_json_serialize, mock_get_conn): # Renamed slightly
    """Tests adding relationship with invalid target node raises IntegrityError."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.execute.side_effect = psycopg.IntegrityError("FK violation")
    mock_json_serialize.return_value = None

    with pytest.raises(psycopg.IntegrityError):
        await rel_queries.add_relationship(mock_conn, "doc:1", "invalid:2", "cites")

    # mock_conn.commit.assert_not_called() # Handled by context manager

@pytest.mark.asyncio
async def test_add_relationship_with_metadata_again(mock_json_serialize, mock_get_conn): # Renamed slightly
    """Tests adding a relationship with metadata."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.fetchone.return_value = (2,) # Simulate returning ID tuple

    metadata = {"certainty": 0.9, "source": "manual"}
    serialized_metadata = '{"certainty":0.9,"source":"manual"}' # Compact
    mock_json_serialize.return_value = serialized_metadata

    result_id = await rel_queries.add_relationship(mock_conn, "chunk:10", "chunk:11", "related_concept", metadata)

    expected_sql = """
        INSERT INTO relationships (source_node_id, target_node_id, relation_type, metadata)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
    """
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("chunk:10", "chunk:11", "related_concept", serialized_metadata))
    # mock_conn.commit.assert_awaited_once() # Handled by context manager
    assert result_id == 2

@pytest.mark.asyncio
async def test_get_relationships_outgoing_cites_again(mock_get_conn): # Renamed slightly
    """Tests getting outgoing 'cites' relationships."""
    mock_conn, mock_cursor = mock_get_conn
    db_results_tuples = [
        (1, 'doc:1', 'doc:2', 'cites', {'page': 5}),
        (3, 'doc:1', 'chunk:10', 'cites', None)
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    relationships = await rel_queries.get_relationships(mock_conn, "doc:1", direction='outgoing', relation_type='cites')

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s) AND relation_type = %s ORDER BY created_at DESC;"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("doc:1", "cites"))
    assert len(relationships) == 2
    assert relationships[0].id == 1
    assert relationships[0].target_node_id == 'doc:2'
    assert relationships[0].metadata == {'page': 5}
    assert relationships[1].id == 3
    assert relationships[1].target_node_id == 'chunk:10'
    assert relationships[1].metadata is None

@pytest.mark.asyncio
async def test_get_relationships_incoming_cites_again(mock_get_conn): # Renamed slightly
    """Tests getting incoming 'cites' relationships."""
    mock_conn, mock_cursor = mock_get_conn
    db_results_tuples = [
        (4, 'doc:5', 'doc:2', 'cites', None)
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    relationships = await rel_queries.get_relationships(mock_conn, "doc:2", direction='incoming', relation_type='cites')

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (target_node_id = %s) AND relation_type = %s ORDER BY created_at DESC;"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, ("doc:2", "cites"))
    assert len(relationships) == 1
    assert relationships[0].id == 4
    assert relationships[0].source_node_id == 'doc:5'
    assert relationships[0].metadata is None

@pytest.mark.asyncio
async def test_get_relationships_specific_type_again(mock_get_conn): # Renamed slightly
    """Tests getting relationships filtered only by type (both directions)."""
    mock_conn, mock_cursor = mock_get_conn
    db_results_tuples = [
        (5, 'chunk:10', 'chunk:11', 'related_concept', None),
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    node_id = "chunk:10"
    rel_type = "related_concept"
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='both', relation_type=rel_type)

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s OR target_node_id = %s) AND relation_type = %s ORDER BY created_at DESC;"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id, node_id, rel_type))
    assert len(relationships) == 1
    assert relationships[0].id == 5

@pytest.mark.asyncio
async def test_get_relationships_direction_both_again(mock_get_conn): # Renamed slightly
    """Tests getting relationships in both directions."""
    mock_conn, mock_cursor = mock_get_conn
    db_results_tuples = [
        (1, 'doc:1', 'doc:2', 'cites', None), # Outgoing
        (4, 'doc:5', 'doc:1', 'cites', None)  # Incoming
    ]
    mock_cursor.fetchall.return_value = db_results_tuples

    node_id = "doc:1"
    relationships = await rel_queries.get_relationships(mock_conn, node_id, direction='both')

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s OR target_node_id = %s) ORDER BY created_at DESC;"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id, node_id))
    assert len(relationships) == 2

@pytest.mark.asyncio
async def test_get_relationships_non_existent_node_again(mock_get_conn): # Renamed slightly
    """Tests getting relationships for a non-existent node returns empty list."""
    mock_conn, mock_cursor = mock_get_conn
    mock_cursor.fetchall.return_value = [] # Simulate no results

    node_id = "nonexistent:999"
    relationships = await rel_queries.get_relationships(mock_conn, node_id) # Default outgoing

    # Exact SQL string from source
    expected_sql = "SELECT id, source_node_id, target_node_id, relation_type, metadata FROM relationships WHERE (source_node_id = %s) ORDER BY created_at DESC;"
    mock_cursor.execute.assert_awaited_once_with(expected_sql, (node_id,))
    assert relationships == []

@pytest.mark.asyncio
async def test_get_relationships_invalid_direction_again(mock_get_conn): # Renamed slightly
    """Tests that an invalid direction raises ValueError."""
    mock_conn, mock_cursor = mock_get_conn

    with pytest.raises(ValueError, match="Invalid direction specified"):
        await rel_queries.get_relationships(mock_conn, "doc:1", direction="sideways")
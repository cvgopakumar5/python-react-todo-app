import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newItem, setNewItem] = useState({ title: '', description: '' });
  const [editingItem, setEditingItem] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const connectionId = useRef(Math.random().toString(36).substr(2, 9));
  const processedMessages = useRef(new Set());
  const cleanupRef = useRef(false);
  const currentItemsRef = useRef([]);
  const addingItemsRef = useRef(new Set());

  // Update the ref whenever items change
  useEffect(() => {
    currentItemsRef.current = items;
  }, [items]);

  // WebSocket connection
  useEffect(() => {
    cleanupRef.current = false;
    
    const connectWebSocket = () => {
      if (cleanupRef.current) return; // Don't connect if component is unmounting
      
      console.log(`[${connectionId.current}] Creating new WebSocket connection...`);
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        if (cleanupRef.current) {
          ws.close();
          return;
        }
        console.log(`[${connectionId.current}] WebSocket connected`);
        setWsConnected(true);
      };

      ws.onmessage = (event) => {
        if (cleanupRef.current) return;
        console.log(`[${connectionId.current}] WebSocket message received:`, event.data);
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onclose = () => {
        if (cleanupRef.current) return;
        console.log(`[${connectionId.current}] WebSocket disconnected`);
        setWsConnected(false);
        // Reconnect after 3 seconds only if not cleaning up
        if (!cleanupRef.current) {
          setTimeout(connectWebSocket, 3000);
        }
      };

      ws.onerror = (error) => {
        if (cleanupRef.current) return;
        console.error(`[${connectionId.current}] WebSocket error:`, error);
        setWsConnected(false);
      };

      wsRef.current = ws;
    };

    connectWebSocket();

    return () => {
      cleanupRef.current = true;
      if (wsRef.current) {
        console.log(`[${connectionId.current}] Closing WebSocket connection...`);
        wsRef.current.close();
      }
    };
  }, []);

  const handleWebSocketMessage = (data) => {
    // Create a unique message identifier
    const messageId = `${data.type}-${data.item?.id || data.item_id}-${data.item?.updated_at || Date.now()}`;
    
    // Check if we've already processed this message
    if (processedMessages.current.has(messageId)) {
      console.log(`[${connectionId.current}] Message already processed, skipping:`, messageId);
      return;
    }
    
    // Mark this message as processed
    processedMessages.current.add(messageId);
    
    // Clean up old messages (keep only last 100)
    if (processedMessages.current.size > 100) {
      const messagesArray = Array.from(processedMessages.current);
      processedMessages.current = new Set(messagesArray.slice(-50));
    }
    
    console.log(`[${connectionId.current}] Processing message:`, data.type, data.item?.id || data.item_id);
    
    switch (data.type) {
      case 'item_created':
        // Check if we're already adding this item
        if (addingItemsRef.current.has(data.item.id)) {
          console.log(`[${connectionId.current}] Item already being added, skipping:`, data.item.id);
          return;
        }
        
        // Mark this item as being added
        addingItemsRef.current.add(data.item.id);
        
        setItems(prev => {
          // Check current items ref for immediate duplicate detection
          const currentItems = currentItemsRef.current;
          const existsInCurrent = currentItems.some(item => item.id === data.item.id);
          
          // Double-check if item already exists to prevent duplicates
          const exists = prev.some(item => item.id === data.item.id) || existsInCurrent;
          if (exists) {
            console.log(`[${connectionId.current}] Item already exists in state, skipping:`, data.item.id);
            // Remove from adding set since we're not adding it
            addingItemsRef.current.delete(data.item.id);
            return prev;
          }
          
          // Additional check: ensure we're not adding a duplicate
          const newItems = [...prev, data.item];
          console.log(`[${connectionId.current}] Adding new item:`, data.item.id, `(Total items: ${newItems.length})`);
          
          // Remove from adding set after successful addition
          setTimeout(() => {
            addingItemsRef.current.delete(data.item.id);
          }, 100);
          
          return newItems;
        });
        break;
      case 'item_updated':
        setItems(prev => {
          const updated = prev.map(item => 
            item.id === data.item.id ? data.item : item
          );
          console.log(`[${connectionId.current}] Updated item:`, data.item.id);
          return updated;
        });
        break;
      case 'item_deleted':
        setItems(prev => {
          const filtered = prev.filter(item => item.id !== data.item_id);
          console.log(`[${connectionId.current}] Deleted item:`, data.item_id);
          return filtered;
        });
        break;
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  // Fetch items on component mount
  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/items`);
      setItems(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch items');
      console.error('Error fetching items:', err);
    } finally {
      setLoading(false);
    }
  };

  const createItem = async (e) => {
    e.preventDefault();
    if (!newItem.title.trim()) return;

    try {
      console.log(`[${connectionId.current}] Creating item:`, newItem.title);
      const response = await axios.post(`${API_BASE_URL}/api/items`, newItem);
      // Don't add to state here since WebSocket will handle it
      setNewItem({ title: '', description: '' });
      setError(null);
    } catch (err) {
      setError('Failed to create item');
      console.error('Error creating item:', err);
    }
  };

  const updateItem = async (itemId, updatedData) => {
    try {
      const response = await axios.put(`${API_BASE_URL}/api/items/${itemId}`, updatedData);
      // Don't update state here since WebSocket will handle it
      setEditingItem(null);
      setError(null);
    } catch (err) {
      setError('Failed to update item');
      console.error('Error updating item:', err);
    }
  };

  const deleteItem = async (itemId) => {
    if (!window.confirm('Are you sure you want to delete this item?')) return;

    try {
      await axios.delete(`${API_BASE_URL}/api/items/${itemId}`);
      // Don't remove from state here since WebSocket will handle it
      setError(null);
    } catch (err) {
      setError('Failed to delete item');
      console.error('Error deleting item:', err);
    }
  };

  const toggleComplete = async (item) => {
    await updateItem(item.id, {
      ...item,
      completed: !item.completed
    });
  };

  const startEditing = (item) => {
    setEditingItem({ ...item });
  };

  const saveEdit = async () => {
    if (!editingItem.title.trim()) return;
    await updateItem(editingItem.id, editingItem);
  };

  const cancelEdit = () => {
    setEditingItem(null);
  };

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="card">
        <h1>Python React Todo App</h1>
        <div style={{ marginBottom: '20px' }}>
          <span className={`status-indicator ${wsConnected ? 'status-online' : 'status-offline'}`}></span>
          {wsConnected ? 'Connected' : 'Disconnected'} (Real-time updates) - Connection ID: {connectionId.current}
        </div>
        
        {error && <div className="error">{error}</div>}

        {/* Add new item form */}
        <form onSubmit={createItem} style={{ marginBottom: '30px' }}>
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              className="form-control"
              value={newItem.title}
              onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
              placeholder="Enter item title"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              className="form-control"
              value={newItem.description}
              onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
              placeholder="Enter item description (optional)"
              rows="3"
            />
          </div>
          <button type="submit" className="btn">Add Item</button>
        </form>

        {/* Items list */}
        <div>
          <h2>Items ({items.length})</h2>
          {items.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#6c757d', marginTop: '20px' }}>
              No items yet. Add one above!
            </p>
          ) : (
            items.map(item => (
              <div key={`item-${item.id}`} className={`item-card ${item.completed ? 'completed' : ''}`}>
                {editingItem && editingItem.id === item.id ? (
                  // Edit mode
                  <div>
                    <div className="form-group">
                      <input
                        type="text"
                        className="form-control"
                        value={editingItem.title}
                        onChange={(e) => setEditingItem({ ...editingItem, title: e.target.value })}
                      />
                    </div>
                    <div className="form-group">
                      <textarea
                        className="form-control"
                        value={editingItem.description}
                        onChange={(e) => setEditingItem({ ...editingItem, description: e.target.value })}
                        rows="2"
                      />
                    </div>
                    <div className="item-actions">
                      <button onClick={saveEdit} className="btn">Save</button>
                      <button onClick={cancelEdit} className="btn btn-secondary">Cancel</button>
                    </div>
                  </div>
                ) : (
                  // View mode
                  <div>
                    <div className="item-title">
                      <input
                        type="checkbox"
                        checked={item.completed}
                        onChange={() => toggleComplete(item)}
                        style={{ marginRight: '10px' }}
                      />
                      {item.title}
                    </div>
                    {item.description && (
                      <div className="item-description">{item.description}</div>
                    )}
                    <div className="item-meta">
                      Created: {new Date(item.created_at).toLocaleString()}
                      {item.updated_at !== item.created_at && (
                        <span> | Updated: {new Date(item.updated_at).toLocaleString()}</span>
                      )}
                    </div>
                    <div className="item-actions">
                      <button onClick={() => startEditing(item)} className="btn btn-secondary">
                        Edit
                      </button>
                      <button onClick={() => deleteItem(item.id)} className="btn btn-danger">
                        Delete
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
import { openDB, DBSchema, IDBPDatabase } from 'idb';

export interface OfflineQueueItem {
  id: string;
  type: 'request';
  payload: {
    url: string;
    method: string;
    headers?: Record<string, string>;
    body?: string;
  };
  timestamp: Date;
  retries: number;
}

interface EpcrDB extends DBSchema {
  offlineQueue: {
    key: string;
    value: OfflineQueueItem;
    indexes: { 'by-timestamp': Date };
  };
}

let db: IDBPDatabase<EpcrDB> | null = null;

export const initDB = async () => {
  db = await openDB<EpcrDB>('epcr-offline', 1, {
    upgrade(database) {
      const store = database.createObjectStore('offlineQueue', {
        keyPath: 'id',
      });
      store.createIndex('by-timestamp', 'timestamp');
    },
  });
};

export const queueRequest = async (
  url: string,
  method: string,
  headers?: Record<string, string>,
  body?: string
): Promise<void> => {
  if (!db) await initDB();
  
  const queueItem: OfflineQueueItem = {
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type: 'request',
    payload: {
      url,
      method,
      headers,
      body,
    },
    timestamp: new Date(),
    retries: 0,
  };

  await db!.add('offlineQueue', queueItem);
};

export const getQueuedItems = async (): Promise<OfflineQueueItem[]> => {
  if (!db) await initDB();
  return await db!.getAllFromIndex('offlineQueue', 'by-timestamp');
};

export const removeQueuedItem = async (id: string): Promise<void> => {
  if (!db) await initDB();
  await db!.delete('offlineQueue', id);
};

export const getQueueSize = async (): Promise<number> => {
  if (!db) await initDB();
  return await db!.count('offlineQueue');
};

export const replayQueue = async (
  onReplay: (item: OfflineQueueItem) => Promise<boolean>
): Promise<void> => {
  if (!db) await initDB();
  const items = await getQueuedItems();
  
  for (const item of items) {
    try {
      const success = await onReplay(item);
      if (success) {
        await removeQueuedItem(item.id);
      } else {
        // Increment retry count
        item.retries += 1;
        if (item.retries >= 5) {
          // Remove after 5 failed attempts
          await removeQueuedItem(item.id);
        } else {
          if (!db) await initDB();
          await db!.put('offlineQueue', item);
        }
      }
    } catch (error) {
      console.error('Failed to replay item', error);
    }
  }
};

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import type { OfflineQueueItem } from '../types';

interface FireMDTDB extends DBSchema {
  offlineQueue: {
    key: string;
    value: OfflineQueueItem;
    indexes: { 'by-timestamp': Date };
  };
}

let db: IDBPDatabase<FireMDTDB> | null = null;

export const initOfflineQueue = async () => {
  db = await openDB<FireMDTDB>('fire-mdt-offline', 1, {
    upgrade(database) {
      const store = database.createObjectStore('offlineQueue', {
        keyPath: 'id',
      });
      store.createIndex('by-timestamp', 'timestamp');
    },
  });
};

export const enqueueOfflineItem = async (
  item: Omit<OfflineQueueItem, 'id' | 'retries'>
): Promise<void> => {
  if (!db) await initOfflineQueue();
  
  const queueItem: OfflineQueueItem = {
    ...item,
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    retries: 0,
  };

  await db!.add('offlineQueue', queueItem);
};

export const getQueuedItems = async (): Promise<OfflineQueueItem[]> => {
  if (!db) await initOfflineQueue();
  return await db!.getAllFromIndex('offlineQueue', 'by-timestamp');
};

export const removeQueuedItem = async (id: string): Promise<void> => {
  if (!db) await initOfflineQueue();
  await db!.delete('offlineQueue', id);
};

export const getQueueSize = async (): Promise<number> => {
  if (!db) await initOfflineQueue();
  return await db!.count('offlineQueue');
};

export const replayQueue = async (
  onReplay: (item: OfflineQueueItem) => Promise<boolean>
): Promise<void> => {
  if (!db) await initOfflineQueue();
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
          if (!db) await initOfflineQueue();
          await db!.put('offlineQueue', item);
        }
      }
    } catch (error) {
      console.error('Failed to replay item', error);
    }
  }
};

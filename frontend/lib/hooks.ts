'use client';

import { useState, useCallback, useEffect } from 'react';
import { useInView } from 'react-intersection-observer';
import type { Article } from '@/lib/mockData';
import { mockData } from '@/lib/mockData';

const AD_FREQUENCY = 3; // Show ad every 3 articles

// Define a type for the ad placeholder
export type Ad = { type: 'ad'; id: string };
export type FeedItem = Article | Ad;

export function useInfiniteFeed(pageSize: number) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const { ref, inView } = useInView({ threshold: 0 });

  const loadMoreItems = useCallback(async () => {
    if (isLoading || !hasMore) return;
    setIsLoading(true);

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 600));

    const start = (page - 1) * pageSize;
    const end = page * pageSize;
    const newArticles = mockData.slice(start, end);

    if (newArticles.length > 0) {
      // Interleave ads with new articles
      const newItems: FeedItem[] = [];
      for (let i = 0; i < newArticles.length; i++) {
        newItems.push(newArticles[i]);
        // Calculate global index to determine ad position
        const globalIndex = start + i + 1;
        if (globalIndex % AD_FREQUENCY === 0 && globalIndex < mockData.length) {
          newItems.push({ type: 'ad', id: `ad-${globalIndex}` });
        }
      }

      setItems((prev) => [...prev, ...newItems]);
      setPage((prev) => prev + 1);
      // Check if there are more articles to fetch from the source
      if (end >= mockData.length) {
        setHasMore(false);
      }
    } else {
      setHasMore(false);
    }

    setIsLoading(false);
  }, [isLoading, hasMore, page, pageSize]);

  // Initial load and subsequent loads on scroll
  useEffect(() => {
    if (inView || page === 1) { // page === 1 for initial load
      loadMoreItems();
    }
  }, [inView, page, loadMoreItems]);

  return { items, isLoading, hasMore, ref };
}

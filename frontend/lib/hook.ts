"use client";

import { useState, useEffect, useCallback } from "react";
import { useInView } from "react-intersection-observer";
import { mockData, type Article } from "./mockData"; // mockData をインポート

// 1. フィードのアイテム型を定義 (記事または広告)
type Ad = {
  type: "ad";
  id: string; // "ad-1", "ad-2" のような一意のID
};
export type FeedItem = Article | Ad;

// 2. 無限スクロールフック
export function useInfiniteFeed(pageSize: number) {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const { ref, inView } = useInView({ threshold: 0 });

  const loadMorePosts = useCallback(async () => {
    if (isLoading || !hasMore) return;
    setIsLoading(true);

    // 0.6秒待機してローディングをシミュレート
    await new Promise((resolve) => setTimeout(resolve, 600));

    // ページに基づいてモックデータを取得
    const start = (page - 1) * pageSize;
    const end = page * pageSize;
    const newArticles = mockData.slice(start, end);

    if (newArticles.length > 0) {
      const newItems: FeedItem[] = [];
      newArticles.forEach((article, index) => {
        newItems.push(article);
        // 記事3件ごと ( (start + index + 1) % 3 ) に広告を挿入
        const globalIndex = start + index + 1;
        if (globalIndex % 3 === 0) {
          newItems.push({ type: "ad", id: `ad-${globalIndex}` });
        }
      });

      setItems((prev) => [...prev, ...newItems]);
      setPage((prev) => prev + 1);
    } else {
      setHasMore(false); // もう読み込むデータがない
    }

    setIsLoading(false);
  }, [isLoading, hasMore, page, pageSize]);

  useEffect(() => {
    if (inView && hasMore && !isLoading) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      loadMorePosts();
    }
  }, [inView, hasMore, isLoading, loadMorePosts]);

  return { items, isLoading, hasMore, ref };
}

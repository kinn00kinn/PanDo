"use client";

import { useEffect } from "react";
import { useInView } from "react-intersection-observer";
import useSWRInfinite from "swr/infinite";
import { fetcher } from "./api";
import type { Article } from "./mockData"; // Article 型は再利用

// 1. フィードのアイテム型を定義 (記事または広告)
type Ad = {
  type: "ad";
  id: string; // "ad-1", "ad-2" のような一意のID
};
export type FeedItem = Article | Ad;

// APIレスポンスの型 (バックエンドの仕様に合わせる)
type ApiResponse = {
  articles: Article[];
  total: number;
  hasMore: boolean;
};

const PAGE_SIZE = 20; // 1ページあたりの記事数

// 2. 無限スクロールフック (SWRバージョン)
export function useInfiniteFeed() {
  const { ref, inView } = useInView({ threshold: 0.5 });

  // SWR Infinite を使ったデータ取得
  const { data, error, size, setSize, isValidating } =
    useSWRInfinite<ApiResponse>(
      // pageIndex: 0から始まるページ番号
      // previousPageData: 前のページのデータ
      (pageIndex, previousPageData) => {
        // --- ループ処理のためのロジック ---
        // データがまだない場合 (初回読み込み)
        if (!data || !data[0]) {
          return `/api/posts?page=${pageIndex + 1}&limit=${PAGE_SIZE}`;
        }

        // 全記事数を取得
        const totalArticles = data[0].total;
        if (!totalArticles) {
          return null; // 記事がなければ停止
        }

        // 総ページ数を計算
        const totalPages = Math.ceil(totalArticles / PAGE_SIZE);
        if (totalPages === 0) {
          return null;
        }

        // ページインデックスをループさせる
        const currentPageIndex = pageIndex % totalPages;
        return `/api/posts?page=${currentPageIndex + 1}&limit=${PAGE_SIZE}`;
      },
      fetcher
    );

  // 取得したデータを単一の配列に加工
  const items: FeedItem[] = data
    ? data.flatMap((page, pageIndex) => {
        const feedItems: FeedItem[] = [];
        page.articles.forEach((article, articleIndex) => {
          // --- IDの重複を避けるための工夫 ---
          // ループによって同じ記事が複数回表示されるため、
          // ページサイズとページインデックスを使ってユニークなIDを生成する
          const uniqueArticle = {
            ...article,
            id: `${article.id}-${pageIndex}`,
          };
          feedItems.push(uniqueArticle);

          // 記事3件ごとに広告を挿入
          const globalIndex = pageIndex * PAGE_SIZE + articleIndex + 1;
          if (globalIndex % 3 === 0) {
            feedItems.push({ type: "ad", id: `ad-${globalIndex}` });
          }
        });
        return feedItems;
      })
    : [];

  // ローディング状態
  const isLoading = isValidating;

  // さらに読み込むデータがあるか (常にtrueにしてループさせる)
  const hasMore = true;

  // 画面下部に到達したら次のページを読み込む
  useEffect(() => {
    // hasMoreのチェックを外して、常に次のページを要求できるようにする
    if (inView && !isLoading) {
      setSize(size + 1);
    }
  }, [inView, isLoading, size, setSize]);

  return { items, isLoading, hasMore, error, ref };
}

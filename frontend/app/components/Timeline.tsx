"use client";

import { useInfiniteFeed, type FeedItem } from "@/lib/hook"; // これでエラーが消えるはず
import ArticleCard from "./ArticleCard";
import AdCard from "./AdCard";
import { Loader2 } from "lucide-react";

// Helper to check item type
function isAd(item: FeedItem): item is { type: "ad"; id: string } {
  return "type" in item && item.type === "ad";
}

const PAGE_SIZE = 4;

export default function Timeline() {
  const { items, isLoading, hasMore, ref } = useInfiniteFeed(PAGE_SIZE);

  return (
    <div className="flex flex-col">
      {/* items を map し、isAd で分岐する */}
      {items.map((item) => {
        if (isAd(item)) {
          return <AdCard key={item.id} />;
        }
        return <ArticleCard key={item.id} article={item} />;
      })}

      {hasMore ? (
        <div
          ref={ref}
          className="flex justify-center items-center py-8 border-b-2 border-black"
        >
          {isLoading && (
            <Loader2 className="animate-spin text-gray-400" size={24} />
          )}
        </div>
      ) : (
        <div className="py-8 text-center text-gray-400 text-sm border-b-2 border-black">
          すべての記事を読み込みました
        </div>
      )}
    </div>
  );
}

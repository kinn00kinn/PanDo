// frontend/src/app/article/[id]/loading.tsx
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

/**
 * 記事詳細ページのスケルトン（ローディングUI）
 */
function ArticleCardSkeleton() {
  return (
    <div className="block w-full p-4 border-b-2 border-black bg-white">
      <div className="flex space-x-3 animate-pulse">
        {/* アイコン */}
        <div className="flex-shrink-0 w-12 h-12 border-2 border-black rounded-full bg-gray-200"></div>
        <div className="flex-1 min-w-0">
          {/* 情報源名 */}
          <div className="h-6 w-1/2 bg-gray-200 rounded mb-2"></div>
          {/* 画像 (あれば) */}
          <div className="mb-2 w-full aspect-video border-2 border-black bg-gray-200 rounded-lg"></div>
          {/* タイトル */}
          <div className="h-7 w-full bg-gray-200 rounded mb-2"></div>
          {/* 本文 */}
          <div className="h-5 w-4/5 bg-gray-200 rounded"></div>
          {/* ボタン類 */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="h-5 w-8 bg-gray-200 rounded"></div>
              <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
              <div className="h-5 w-8 bg-gray-200 rounded"></div>
              <div className="h-5 w-8 bg-gray-200 rounded"></div>
            </div>
            <div className="h-4 w-16 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * コメント欄のスケルトン
 */
function CommentListSkeleton() {
  const skeletons = [1, 2]; // 2件分のスケルトンを表示
  return (
    <div className="flex flex-col">
      {skeletons.map((i) => (
        <div key={i} className="p-4 border-b-2 border-black flex space-x-3 animate-pulse">
          <div className="flex-shrink-0 rounded-full bg-gray-200 w-10 h-10 border-2 border-black"></div>
          <div className="flex-1 space-y-2">
            <div className="h-4 w-1/3 bg-gray-200 rounded"></div>
            <div className="h-4 w-full bg-gray-200 rounded"></div>
          </div>
        </div>
      ))}
      {/* コメントフォームのローディング */}
      <div className="p-4 border-y-2 border-black flex justify-center">
        <Loader2 className="animate-spin text-gray-400" />
      </div>
    </div>
  );
}


/**
 * article/[id] ページ専用のローディングコンポーネント
 */
export default function Loading() {
  return (
    <div className="flex justify-center bg-white text-black">
      <div className="w-full max-w-xl">
        {/* ヘッダー (固定) */}
        <header className="sticky top-0 z-10 bg-white/90 backdrop-blur-sm p-2 border-b-2 border-black">
          <Link
            href="/"
            className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded-full"
            aria-disabled="true" // ローディング中は無効
          >
            <ArrowLeft size={20} />
            <span className="font-bold">戻る</span>
          </Link>
        </header>

        {/* メインコンテンツ (スケルトン) */}
        <main className="border-x-2 border-b-2 border-black">
          <ArticleCardSkeleton />
          <CommentListSkeleton />
        </main>
      </div>
    </div>
  );
}
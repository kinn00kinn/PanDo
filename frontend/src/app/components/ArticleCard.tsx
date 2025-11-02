"use client"; // ★ クライアントコンポーネントに変更

import type { Article } from "@/app/lib/mockData";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import Image from "next/image";
import UserIcon from "./UserIcon";
import { Share2 } from "lucide-react"; // ★ 共有アイコンをインポート
import { useState } from "react"; // ★ useStateをインポート

type ArticleCardProps = {
  article: Article & { summary?: string | null };
};

export default function ArticleCard({ article }: ArticleCardProps) {
  const timeAgo = formatDistanceToNow(new Date(article.published_at), {
    addSuffix: true,
    locale: ja,
  });

  // --- 動的スタイルロジック ---
  const hasSummary = article.summary && article.summary.length > 0;
  const titleLineClamp = hasSummary ? "line-clamp-1" : "line-clamp-2";

  // ★ 追加: コピー状態を管理
  const [copied, setCopied] = useState(false);

  // ★ 追加: 共有ボタンのクリック処理
  const handleShareClick = async (e: React.MouseEvent) => {
    // カード全体 (<a> タグ) のリンク遷移を防ぐ
    e.preventDefault();
    e.stopPropagation();

    // Markdown形式でテキストを作成
    const markdownLink = `[${article.title}](${article.article_url})`;

    try {
      // クリップボードにコピー
      await navigator.clipboard.writeText(markdownLink);
      setCopied(true);

      // 2秒後に「共有」に戻す
      setTimeout(() => {
        setCopied(false);
      }, 2000);
    } catch (err) {
      console.error("クリップボードへのコピーに失敗しました:", err);
      // エラー時のフィードバック（例: アラートやトースト）をここに追加できます
    }
  };

  return (
    <a
      href={article.article_url}
      target="_blank"
      rel="noopener noreferrer"
      className="block w-full p-4 border-b-2 border-black bg-white transition-colors duration-150 hover:bg-gray-50"
    >
      <div className="flex space-x-3">
        {/* 1. 左側: アイコン */}
        <div className="flex-shrink-0">
          <UserIcon sizePx={48} />
        </div>

        {/* 2. 右側: コンテンツ */}
        <div className="flex-1 min-w-0">
          {/* 上部: ユーザー名と投稿時間 */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            <span className="font-bold text-lg text-black truncate">
              {article.source_name}
            </span>
            <span className="flex-shrink-0">· {timeAgo}</span>
          </div>

          {/* 画像 (あれば表示) */}
          {article.image_url && (
            <div className="mb-2 w-full border-2 border-black flex items-center justify-center overflow-hidden rounded-lg">
              <Image
                src={article.image_url}
                alt={article.title}
                width={700}
                height={400}
                className="w-full h-auto object-cover max-h-96"
              />
            </div>
          )}

          {/* テキスト (タイトルと要約) */}
          <div className="space-y-1">
            <h2 className={`text-xl font-bold ${titleLineClamp}`}>
              {article.title}
            </h2>
            {hasSummary && (
              <p className="text-gray-700 line-clamp-2">{article.summary}</p>
            )}
          </div>

          {/* ★ 修正: 共有ボタンの追加 */}
          <div className="mt-4 flex items-center space-x-4 text-black">
            {/* 他のボタン（いいねなど）をここに追加可能 */}
            {/* <div className="flex items-center space-x-1 cursor-pointer hover:text-gray-600">
       <ThumbsUp size={18} />
       <span className="text-sm">123</span>
      </div> */}

            {/* 共有ボタン */}
            <button
              onClick={handleShareClick}
              // コピー中はボタンを無効化し、色を変える
              disabled={copied}
              className={`flex items-center space-x-1 transition-colors duration-150 ${
                copied
                  ? "text-green-600" // コピー完了時の色
                  : "text-black hover:text-gray-600 cursor-pointer" // 通常時の色
              }`}
            >
              <Share2 size={18} />
              {/* テキストを状態で切り替え */}
              <span className="text-sm">
                {copied ? "コピーしました！" : "共有 (MD)"}
              </span>
            </button>
          </div>
        </div>
      </div>
    </a>
  );
}

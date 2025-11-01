import type { Article } from "@/lib/mockData";
import { formatDistanceToNow } from "date-fns";
import { ja } from "date-fns/locale";
import Image from "next/image";
// import UserIcon from "./UserIcon"; // ★ 作成したアイコン
import { Star } from "lucide-react"; // ★ いいねアイコン

type ArticleCardProps = {
  article: Article;
};

export default function ArticleCard({ article }: ArticleCardProps) {
  const timeAgo = formatDistanceToNow(new Date(article.published_at), {
    addSuffix: true,
    locale: ja,
  });

  return (
    // ★ カード全体のスタイル: 上下左右の境界線、背景は白
    <a
      href={article.article_url}
      target="_blank"
      rel="noopener noreferrer"
      className="block w-full p-4 border-b-2 border-black bg-white cursor-pointer transition-colors duration-150 hover:bg-gray-50"
    >
      {/* 上部: ユーザーアイコンとユーザー名 */}
      <div className="flex items-center space-x-3 mb-3">
        {/* <UserIcon size={10} /> ★ アイコン表示 */}
        <span className="font-bold text-lg">{article.source_name}</span>{" "}
        {/* ユーザー名 */}
      </div>

      {/* 中部: 画像 (あれば表示) */}
      <div className="w-full border-2 border-black flex items-center justify-center overflow-hidden">
        {article.image_url ? (
          <Image
            src={article.image_url}
            alt={article.title}
            width={700} // ★ 可能な最大幅
            height={400} // ★ 適切な高さ
            className="w-full h-auto object-cover max-h-96" // ★ 画像の表示調整
          />
        ) : (
          // 画像がない場合のプレースホルダー
          <div className="w-full h-48 bg-gray-100 flex items-center justify-center text-gray-400 text-xl font-bold">
            NO IMAGE
          </div>
        )}
      </div>

      {/* 下部: タイトルと要約、日付 */}
      <div className="mt-3">
        <h2 className="text-xl font-bold line-clamp-2">{article.title}</h2>
        <p className="mt-1 text-base text-gray-700 line-clamp-3">
          {article.summary}
        </p>
        <div className="mt-2 flex items-center text-sm text-gray-500">
          <span>{timeAgo}</span>
          <span className="ml-auto flex items-center space-x-1">
            <Star size={16} className="text-black" />
          </span>
        </div>
      </div>
    </a>
  );
}

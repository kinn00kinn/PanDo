import { Star, Share2 } from "lucide-react";
import UserIcon from "./UserIcon"; // ★ 新しいアイコンをインポート

export default function AdCard() {
  return (
    <div className="block w-full p-4 border-b-2 border-black bg-white">
      <div className="flex space-x-3">
        {/* 1. 左側: アイコン */}
        <div className="flex-shrink-0">
          <UserIcon sizePx={48} />
        </div>

        {/* 2. 右側: コンテンツ */}
        <div className="flex-1 min-w-0">
          {/* 上部: ユーザー名と広告表示 */}
          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-2">
            <span className="font-bold text-lg text-black truncate">
              広告主
            </span>
            <span className="flex-shrink-0 ml-auto">広告</span>
          </div>

          {/* 中部: テキスト (タイトルと要約) */}
          <div className="space-y-1">
            <h2 className="text-xl font-bold line-clamp-2">
              AI開発を加速する強力なツール！
            </h2>
            <p className="text-base text-gray-700 line-clamp-3">
              最新のAIソリューションで、あなたのプロジェクトに革命を起こしましょう。今すぐ無料体験！
            </p>
          </div>

          {/* 中部: 広告画像 (ダミー) */}
          <div className="mt-3 w-full border-2 border-black flex items-center justify-center overflow-hidden rounded-lg h-48 bg-gray-100 text-gray-400 text-xl font-bold">
            ここに広告画像
          </div>
        </div>
      </div>
    </div>
  );
}

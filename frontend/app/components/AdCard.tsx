import { Megaphone, Star } from "lucide-react";
// import UserIcon from "./UserIcon"; // ★ UserIcon をインポート

export default function AdCard() {
  return (
    <div className="w-full p-4 border-b-2 border-black bg-white text-black">
      {/* 上部: ユーザーアイコンと広告表示 */}
      <div className="flex items-center space-x-3 mb-3">
        {/* <UserIcon size={10} /> */}
        <span className="font-bold text-lg">広告主</span>
        <span className="ml-auto text-sm text-gray-500">広告</span>
      </div>

      {/* 中部: 広告画像 (今回はダミー) */}
      <div className="w-full border-2 border-black flex items-center justify-center overflow-hidden h-48 bg-gray-100 text-gray-400 text-xl font-bold">
        ここに広告画像
      </div>

      {/* 下部: 広告テキストといいねアイコン */}
      <div className="mt-3">
        <h2 className="text-xl font-bold line-clamp-2">
          AI開発を加速する強力なツール！
        </h2>
        <p className="mt-1 text-base text-gray-700 line-clamp-3">
          最新のAIソリューションで、あなたのプロジェクトに革命を起こしましょう。今すぐ無料体験！
        </p>
        <div className="mt-2 flex items-center text-sm text-gray-500">
          <span>プロモーション</span>
          <span className="ml-auto flex items-center space-x-1">
            <Star size={16} className="text-black" />
          </span>
        </div>
      </div>
    </div>
  );
}

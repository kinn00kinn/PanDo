import Timeline from "@/app/components/Timeline";
import { RefreshCcw, SquarePen } from "lucide-react"; // ★ アイコンをインポート

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center bg-white text-black">
      {/* ヘッダー: Xライクな上部固定ヘッダー */}
      <header className="w-full max-w-xl md:max-w-2xl bg-white sticky top-0 z-10">
        <div className="flex justify-between items-center px-4 py-3 border-b-2 border-black">
          {" "}
          {/* ★ 境界線を太く */}
          <h1 className="text-2xl font-bold">NScroller</h1> {/* ★ ロゴ */}
        </div>
      </header>

      {/* メインコンテンツのラッパー */}
      <div className="w-full max-w-xl md:max-w-2xl border-x-2 border-black">
        {" "}
        {/* ★ 左右に太い境界線 */}
        <Timeline />
      </div>
    </main>
  );
}

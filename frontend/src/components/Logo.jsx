export default function Logo() {
  return (
    <div className="flex items-center gap-4">
      <div className="grid h-12 w-12 place-items-center rounded-md bg-pepper text-lg font-black text-white">
        H
      </div>
      <div>
        <h1 className="text-2xl font-black leading-none">하리풀</h1>
        <p className="mt-2 text-sm text-pepper">하루에 리트 1문제 풀기</p>
      </div>
    </div>
  );
}

const cells = Array.from({ length: 84 }, (_, index) => index);

export default function ActivityGrid() {
  return (
    <div className="grid max-w-[250px] grid-cols-[repeat(14,minmax(0,1fr))] gap-1.5">
      {cells.map((index) => (
        <div
          key={index}
          className={`h-3 w-3 rounded-[3px] ${
            index % 13 === 0 || index % 17 === 0 ? "bg-pepper" : index % 5 === 0 ? "bg-smoke" : "bg-ash"
          }`}
        />
      ))}
    </div>
  );
}

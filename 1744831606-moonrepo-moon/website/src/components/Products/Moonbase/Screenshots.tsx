export default function Screenshots() {
	return (
		<>
			<div className="overflow-hidden rounded-lg w-[100%] sm:w-[65%] md:w-full lg:w-[75%] bg-[#000e19] p-1">
				<img src="/img/home/org.png" alt="moonbase - organization view" className="block" />
			</div>

			<div className="overflow-hidden rounded-lg w-[100%] sm:w-[65%] md:w-full lg:w-[75%] bg-[#000e19] p-1 absolute bottom-0 right-0 z-10 hidden sm:block">
				<img src="/img/home/repo.png" alt="moonbase - repository view" className="block" />
			</div>
		</>
	);
}

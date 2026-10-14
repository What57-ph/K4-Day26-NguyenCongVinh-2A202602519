"""MCP CLIENT minh hoạ — kết nối tới weather_server.py qua giao thức MCP.

Điểm mấu chốt: client KHÔNG hard-code tool. Nó hỏi server "anh có tool gì?"
(list_tools) tại runtime, rồi gọi tool (call_tool) để SERVER thực thi và trả
kết quả về qua MCP.

Ví dụ này không cần ANTHROPIC_API_KEY — nó cho thấy lớp giao thức MCP hoạt
động độc lập với model. (Trong thực tế, một LLM sẽ dùng Function Calling để
quyết định khi nào gọi tool đã khám phá được.)

Cách chạy (cùng thư mục với weather_server.py, client tự khởi động server):
    pip install -r ../requirements.txt
    python weather_client.py
"""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Dùng đúng interpreter đang chạy client (tránh lỗi "python" không tồn tại)
    params = StdioServerParameters(command=sys.executable, args=["weather_server.py"])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. KHÁM PHÁ tool mà server công bố (không hard-code)
            tools = await session.list_tools()
            print("Tools server cung cấp:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")

            # 2. Tạo đối số từ schema và gọi bằng tên server đã công bố
            for city in ["Hanoi", "Danang", "Haiphong"]:
                for tool in tools.tools:
                    schema = tool.input_schema
                    required = schema.get("required", [])
                    args = {}
                    for name, spec in schema.get("properties", {}).items():
                        if name in required:
                            args[name] = city if spec.get("type") == "string" else 3

                    result = await session.call_tool(tool.name, args)
                    print(f"\ncall_tool {tool.name}({args}):")
                    print("  ->", result.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())

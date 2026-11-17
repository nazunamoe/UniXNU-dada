/* SPDX-License-Identifier: MIT */
/* Link stubs for hooks the dada kernel does not provide.
 *
 * NativeGOPPresenter (the CPU display service) declares the GPU trace entry points optional, but the kernel link
 * still needs a definition: dada has no Adreno driver, whose NativeGpuTrace.inc normally supplies them. Tracing is
 * reported off and every record or pixel piece is dropped. */
#include <stdint.h>

int native_gpu_trace_enabled(void) { return 0; }

void native_gpu_trace_record(uint32_t event, uint32_t pid, const uint64_t *values, uint32_t count)
{
	(void)event; (void)pid; (void)values; (void)count;
}

int native_gpu_pixel_put(const void *piece, uint32_t pid)
{
	(void)piece; (void)pid;
	return 0;
}

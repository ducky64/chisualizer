#include "Fix3Stage.h"

int main() {
	Fix3Stage_t myModule;
	Fix3Stage_api_t myApi;
	myApi.init(&myModule);
	myApi.read_eval_print_loop();

	return 0;
}

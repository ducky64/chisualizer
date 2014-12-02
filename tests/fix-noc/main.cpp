#include "FixNetwork2d.h"

int main() {
	FixNetwork2d_t myDut;
	FixNetwork2d_api_t myDutApi;
	myDutApi.init(&myDut);
	myDutApi.read_eval_print_loop();

	return 0;
}

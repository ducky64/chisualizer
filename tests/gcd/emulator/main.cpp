#include "GCD.h"

int main() {
	GCD_t myGcd;
	GCD_api_t myGcdApi;
	myGcdApi.init(&myGcd);
	myGcdApi.read_eval_print_loop();

	return 0;
}

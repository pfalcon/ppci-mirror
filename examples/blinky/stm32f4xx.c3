
module stm32f4xx;

public type struct {
    int MODER;
    int OTYPER;
    int OSPEEDR;
    int PUPDR;
    int IDR;
    int ODR;
    int BSRR;
}* GPIO_Type;

public type struct {
    int CR;
    int PLLCFGR;
    int CFGR;
    int CIR;
    int AHB1RSTR;
    int AHB2RSTR;
    int AHB3RSTR;
    int reserved0;
    int APB1RSTR;
    int APB2RSTR;
    int reserved1a, reserved1b;
    int AHB1ENR;
    int AHB2ENR;
    int AHB3ENR;
    int reserved2;
    int APB1ENR, APB2ENR;
}* RCC_Type;

public type struct {
    int ISER0;
    int ISER1;
}* NVIC_Type;

public type struct {
    int CTRL;
    int LOAD;
    int CURRENT;
    int CALIB;
}* Systick_Type;


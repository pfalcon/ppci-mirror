/* Test the various methods of initialization in C.

Notes:
- global and local initialization is syntactically the same
  but the code is fully different.

*/

#include <stdio.h>

int x = 3;
char c0[] = "abc";
char c1[9] = "abc";
char c2[3] = "abc";
char c3[4] = "abc";
int g_i = (7 & 5) ^ 15;

enum E { ONE, TWO, THREE };

enum E g_e0;
enum E g_e1 = THREE;
enum E g_e2 = 1;

void main_main()
{
  int y = x * 3;
  printf("%d\n", x);
  printf("%d\n", y);
  printf("%d\n", 99);

  // TODO: make this work: printf("%c %c %d\n", c1[0], c1[2], sizeof(c1));
  printf("%c %c\n", c0[0], c0[2]);
  printf("%d\n", sizeof(c0));

  printf("%c %c\n", c1[0], c1[2]);
  printf("%d\n", sizeof(c1));

  printf("%c %c\n", c2[0], c2[2]);
  printf("%d\n", sizeof(c2));

  printf("%c %c\n", c3[0], c3[2]);
  printf("%d\n", sizeof(c3));

  printf("g_i = %d\n", g_i);

  enum E e0;
  enum E e1 = THREE;
  enum E e2 = 1;

  printf("g_e1 = %d\n", g_e1);
  printf("g_e2 = %d\n", g_e2);

  printf("e1 = %d\n", e1);
  printf("e2 = %d\n", e2);

}


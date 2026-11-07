#import "../../templates/handout.typ": handout, problem

#let session = json("session.json")

#handout(
  title: session.title,
  date: session.date.split("-").rev().join("."),
  [
  #problem(1, "ВсОШ, муниципальный этап, Новосибирская обл., 2025/26, задача 2", "https://tasks.olimpiada.ru/upload/files/tasks/72/2025/tasks-math-10-mun-novosb-25-26.pdf#page=1")[
    В треугольнике $A B C$ центр описанной окружности $O$, #box($angle A B C = 60 degree$), #box($angle C B O = 45 degree$). Прямые $B O$ и $A C$ пересекаются в $P$. Докажите, что #box($A P = P O$).
  ]

  #problem(2, "ВсОШ, региональный этап, 2012, задача 2", "https://olympiads.mccme.ru/vmo/2012/iii-day1.pdf#page=2")[
    В выпуклом шестиугольнике $A B C D E F$ #box($angle F A E = angle B D C$), а четырёхугольники $A B D F$ и $A C D E$ вписанные. Докажите, что #box($B F parallel C E$).
  ]

  #problem(3, "ВсОШ, региональный этап, 2015, задача 6", "https://olympiads.mccme.ru/vmo/2015/iii-day2.pdf#page=2")[
    В прямоугольном треугольнике $A B C$ с #box($angle C = 90 degree$) проведена биссектриса $B K$, #box($K in A C$). Окружность $A B K$ вторично пересекает сторону $B C$ в $L$. Докажите, что #box($C B + C L = A B$).
  ]

  #problem(4, "ВсОШ, региональный этап, 2019, задача 8", "https://olympiads.mccme.ru/vmo/2019/iii-day2.pdf#page=2")[
    В остроугольном треугольнике $A B C$ проведена высота $B H$. Точки $M$ и $N$ - середины $A H$ и $C H$. В окружности $B M N$ проведён диаметр $B B_0$. Докажите, что #box($A B_0 = C B_0$).
  ]

  #problem(5, "ВсОШ, региональный этап, 2016, задача 3", "https://olympiads.mccme.ru/vmo/2016/iii-day1.pdf#page=2")[
    На сторонах $A B$ и $C D$ выпуклого четырёхугольника $A B C D$ взяты точки в порядке $A, K, L, B$ и $C, M, N, D$. Известно, что #box($A K = K N = D N$) и #box($B L = B C = C M$). Докажите: если $B C N K$ вписанный, то $A D M L$ тоже вписанный.
  ]

  #problem(6, "ВсОШ, региональный этап, 2015, задача 3", "https://olympiads.mccme.ru/vmo/2015/iii-day1.pdf#page=2")[
    $A L$ - биссектриса треугольника $A B C$. Серединный перпендикуляр к $A L$ пересекает окружность $A B C$ в $P$ и $Q$. Докажите, что окружность $P L Q$ касается стороны $B C$.
  ]

  #problem(7, "ВсОШ, региональный этап, 2022, задача 7", "https://olympiads.mccme.ru/vmo/2022/iii-2.pdf#page=12")[
    Вписанный четырёхугольник $A B C D$ удовлетворяет #box($angle A = 2 angle B$). Биссектриса угла $C$ пересекает сторону $A B$ в $E$. Докажите, что #box($A D + A E = B E$).
  ]

  #problem(8, "МОШ, 2022, задача 2", "https://mmo.mccme.ru/2022/mmo2022-var10.pdf#page=1")[
    $M$ и $N$ - середины сторон $A B$ и $A C$ треугольника $A B C$. Касательная $ell$ к окружности $A B C$ в $A$ пересекает прямую $B C$ в $K$. Докажите, что окружность $M K N$ касается $ell$.
  ]

  #problem(9, "ВсОШ, региональный этап, 2023, задача 8", "https://zsfond.ru/wp-content/uploads/2023/02/usloviya-ii-tur-10-klass.pdf#page=1")[
    Биссектриса $A K$ угла $A$ параллелограмма $A B C D$ пересекает сторону $B C$ в $K$. На $A B$ выбрана $L$ так, что #box($A L = C K$). Отрезки $A K$ и $C L$ пересекаются в $M$. Точка $N$ лежит на продолжении $A D$ за $D$, а $A L M N$ вписанный. Докажите, что #box($angle C N L = 90 degree$).
  ]

  #problem(10, "МОШ, 2023, задача 3", "https://mmo.mccme.ru/2023/mmo2023-var10.pdf#page=1")[
    Периметр треугольника $A B C$ равен 1. Окружность касается стороны $B C$ и продолжений $A B$ и $A C$ в точках $P$ и $Q$. Прямая через середины $A B$ и $A C$ пересекает окружность $A P Q$ в $X$ и $Y$. Найдите $X Y$.
  ]
  ],
)

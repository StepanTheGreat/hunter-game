from ward import test, raises

from plugin import *

def test_runner(app: App):
    "A basic runner that will be used for tests"
    app.startup()
    app.update(1)
    app.render()
    app.finalize()


@test("Systems at every schedule must be executed")
def _():
    # In this test we will check if every single system at every schedule works as intended

    SCHEDULES = (
        Schedule.Startup,
        Schedule.First,
        Schedule.PreUpdate,
        Schedule.Update,
        Schedule.FixedUpdate,
        Schedule.PostUpdate,
        Schedule.PreDraw,
        Schedule.Draw,
        Schedule.PostDraw,
        Schedule.Last,
        Schedule.Finalize,
    )

    number = [0]

    def add_one(_):
        number[0] += 1

    class TestPlugin(Plugin):
        def build(self, app):
            app.set_runner(test_runner)
            for schedule in SCHEDULES:
                app.add_systems(schedule, add_one)

    app = App(AppBuilder(TestPlugin()))
    app.run()

    assert number[0] == len(SCHEDULES)

@test("Only events with @event decorators can pass")
def _():

    class WrongEvent:
        pass

    def send_wrong_event(resources: Resources):
        with raises(AssertionError):
            resources[EventWriter].push_event(WrongEvent())

    class TestPlugin(Plugin):
        def build(self, app):
            app.add_systems(Schedule.Startup, send_wrong_event)
            app.set_runner(test_runner)

    app = App(AppBuilder(TestPlugin()))
    app.run()

@test("Event listeners must receive events")
def _():
    @event
    class TestEvent:
        pass

    @event
    class TestEvent2:
        pass
    
    invoked = [False]

    def test_listener(_, event):
        invoked[0] = True

    def send_event(resources: Resources):
        resources[EventWriter].push_event(TestEvent())

    class TestPlugin(Plugin):
        def build(self, app):
            app.add_systems(Schedule.Startup, send_event)
            app.add_event_listener(TestEvent, test_listener)
            app.set_runner(test_runner)

    app = App(AppBuilder(TestPlugin()))
    app.run()

    assert invoked[0] == True

@test("Proper systems ordering based on their priority")
def _():    
    invoked = []

    one = lambda _: invoked.append(1)
    two = lambda _: invoked.append(2)
    three = lambda _: invoked.append(3)
    four = lambda _: invoked.append(4)
    five = lambda _: invoked.append(5)

    class TestPlugin(Plugin):
        def build(self, app):
            # Five should be called last
            app.add_systems(Schedule.Startup, five, priority=5)

            # These 3 systems are all added on priority 2, so their order should be preserved
            app.add_systems(Schedule.Startup, two, three, four, priority=2)

            # Although we add the first system last - since it by default will be executed at priority 0 - 
            # it will actually be the first system to run
            app.add_systems(Schedule.Startup, one)

            app.set_runner(test_runner)

    app = App(AppBuilder(TestPlugin()))
    app.run()

    assert invoked == [1, 2, 3, 4, 5]
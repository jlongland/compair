// Use the external Chai As Promised to deal with resolving promises in
// expectations
var chai = require('chai');
var chaiAsPromised = require('chai-as-promised');
chai.use(chaiAsPromised);

var expect = chai.expect;

var editCourseUserStepDefinitionsWrapper = function () {

    this.Then("I should see '$count' users listed for the course", function (count) {
        count = parseInt(count);
        return expect(element.all(by.repeater("user in classlist | orderBy:[predicate, 'firstname', 'lastname'] | emptyToEnd:predicate | orderBy:'':reverse"))
            .count()).to.eventually.eql(count);
    });

    this.Then("I should see course users with displaynames:", function (data) {
        var list = data.hashes().map(function(item) {
            // add the " »" that is displayed on the page
            return item.displayname;
        });

        return expect(element.all(by.repeater("user in classlist | orderBy:[predicate, 'firstname', 'lastname'] | emptyToEnd:predicate | orderBy:'':reverse")
            .column('user.displayname')).getText()).to.eventually.eql(list);
    });

    this.When("I select the first user search result", function () {
        return element(by.repeater('match in matches track by $index').row(0)).click();
    });


    this.When("I select the Student role for the user", function () {
        var fillElement = element(by.css("#enrol-select-course-role"));

        if (browser.browserName == "firefox") {
            fillElement.click();
        }
        fillElement.sendKeys("Student");

        // force blur
        return element(by.css("body")).click();
    });

    this.When("I sort by displayname in decending order", function () {
        return element(by.cssContainingText("table th a", "Display Name")).click().click();
    });

    this.When("I set the second user's group to '$groupname'", function (groupname) {
        var groupSelect = element.all(by.repeater("user in classlist | orderBy:[predicate, 'firstname', 'lastname'] | emptyToEnd:predicate | orderBy:'':reverse"))
            .get(1)
            .element(by.model('user.group_name'));
        if (browser.browserName == "firefox") {
            groupSelect.click();
        }

        groupSelect.sendKeys(groupname);
        // force blur
        return element(by.css("h1")).click();
    });

    this.Given("I drop the second user from the course", function () {
        element.all(by.repeater("user in classlist | orderBy:[predicate, 'firstname', 'lastname'] | emptyToEnd:predicate | orderBy:'':reverse"))
            .get(1)
            .element(by.cssContainingText('a', 'Drop'))
            .click();

        browser.wait(protractor.ExpectedConditions.alertIsPresent(), 1000);

        browser.driver.switchTo().alert().accept();
        browser.driver.switchTo().defaultContent();
        return element(by.css("body")).click();
    });
};

module.exports = editCourseUserStepDefinitionsWrapper;